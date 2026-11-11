"""Команды эмулятора: ls, cd, history, who, head, touch, rm, exit, vfs-info.

Каждая команда - функция ``cmd_*(shell, args)``, которая возвращает
``Result`` или бросает ``CommandError`` с готовым сообщением об ошибке.
"""
from result import CommandError, Result
from vfs import join_path, normalize

HEAD_DEFAULT_LINES = 10
HOME_PARTS = ["home", "user"]
MAX_CD_ARGS = 1
MAX_HISTORY_ARGS = 1
NOT_FOUND = "Нет такого файла или каталога"
NOT_DIR = "Не является каталогом"


def _parse_flags(args, allowed, name):
    """Разбирает ключи (-l, -la); возвращает (ключи, операнды)."""
    flags, operands = set(), []
    for arg in args:
        if not arg.startswith("-") or arg == "-":
            operands.append(arg)
            continue
        unknown = sorted(set(arg[1:]) - set(allowed))
        if unknown:
            raise CommandError(f"{name}: неверный ключ -- '{unknown[0]}'")
        flags.update(arg[1:])
    return flags, operands


def home_path(vfs):
    """Домашняя папка VFS: /home/user, если она есть, иначе корень."""
    node = vfs.get(HOME_PARTS)
    if node is not None and node.is_dir:
        return join_path(HOME_PARTS)
    return "/"


def cmd_cd(shell, args):
    """cd [путь]: переходит в папку VFS; без аргумента - в домашнюю."""
    if len(args) > MAX_CD_ARGS:
        raise CommandError("cd: слишком много аргументов")
    target = args[0] if args else home_path(shell.vfs)
    parts = normalize(shell.cwd, target)
    node = shell.vfs.get(parts)
    if node is None:
        raise CommandError(f"cd: {target}: {NOT_FOUND}")
    if not node.is_dir:
        raise CommandError(f"cd: {target}: {NOT_DIR}")
    shell.cwd = parts
    return Result()


def _format_entry(name, node, long_format):
    """Форматирует запись ls: коротко или с типом и размером."""
    if not long_format:
        return name
    kind = "d" if node.is_dir else "-"
    size = 0 if node.is_dir else len(node.data)
    return f"{kind} {size:>6} {name}"


def _dir_listing(node, flags):
    """Возвращает текст содержимого папки с учётом ключей -l и -a."""
    show_hidden = "a" in flags
    long_format = "l" in flags
    names = [name for name in sorted(node.children)
             if show_hidden or not name.startswith(".")]
    entries = [_format_entry(name, node.children[name], long_format)
               for name in names]
    return ("\n" if long_format else "  ").join(entries)


def _ls_block(path, node, flags, header):
    """Возвращает вывод ls для одного пути."""
    if node.is_dir:
        body = _dir_listing(node, flags)
        return f"{path}:\n{body}" if header else body
    return _format_entry(path, node, "l" in flags)


def cmd_ls(shell, args):
    """ls [-l] [-a] [путь...]: содержимое папки или сведения о файле."""
    flags, paths = _parse_flags(args, "la", "ls")
    header = bool(paths[1:])
    blocks, errors = [], []
    for path in paths or ["."]:
        node = shell.vfs.get(normalize(shell.cwd, path))
        if node is None:
            errors.append(
                f"ls: невозможно получить доступ к '{path}': {NOT_FOUND}")
        else:
            blocks.append(_ls_block(path, node, flags, header))
    return Result("\n".join(errors + blocks), ok=not errors)


def cmd_history(shell, args):
    """history [N]: нумерованный список введённых команд."""
    if len(args) > MAX_HISTORY_ARGS:
        raise CommandError("history: слишком много аргументов")
    entries = list(enumerate(shell.history, 1))
    if args:
        if not args[0].isdigit():
            raise CommandError(
                f"history: {args[0]}: требуется числовой аргумент")
        limit = int(args[0])
        entries = entries[-limit:] if limit else []
    return Result("\n".join(f"{num:>5}  {text}" for num, text in entries))


def cmd_who(shell, args):
    """who [-q]: пользователи, работающие в эмуляторе."""
    flags, operands = _parse_flags(args, "q", "who")
    if operands:
        raise CommandError(f"who: лишний операнд '{operands[0]}'")
    if "q" in flags:
        return Result(f"{shell.user}\n# users=1")
    stamp = shell.login_time.strftime("%Y-%m-%d %H:%M")
    return Result(f"{shell.user}  console  {stamp} ({shell.host})")


def _head_count(text):
    """Преобразует аргумент ключа -n в число строк."""
    if text is None:
        raise CommandError("head: ключ -n требует аргумент")
    if not text.isdigit():
        raise CommandError(f"head: неверное число строк: '{text}'")
    return int(text)


def _parse_head(args):
    """Возвращает (число строк, список файлов) для head."""
    count, files = HEAD_DEFAULT_LINES, []
    items = iter(args)
    for arg in items:
        if arg == "-n":
            count = _head_count(next(items, None))
        elif arg.startswith("-n"):
            count = _head_count(arg[2:])
        elif arg.startswith("-") and arg != "-":
            raise CommandError(f"head: неверный ключ -- '{arg[1:]}'")
        else:
            files.append(arg)
    return count, files


def _read_text(shell, name):
    """Читает файл VFS как текст (двоичные данные - в base64)."""
    node = shell.vfs.get(normalize(shell.cwd, name))
    if node is None:
        raise CommandError(f"head: невозможно открыть '{name}': {NOT_FOUND}")
    if node.is_dir:
        raise CommandError(f"head: ошибка чтения '{name}': Это каталог")
    return node.as_text()


def cmd_head(shell, args):
    """head [-n N] файл...: первые N строк файлов (по умолчанию 10)."""
    count, files = _parse_head(args)
    if not files:
        raise CommandError("head: не указан файл")
    header = bool(files[1:])
    blocks, errors = [], []
    for name in files:
        try:
            lines = _read_text(shell, name).splitlines()[:count]
        except CommandError as err:
            errors.append(str(err))
            continue
        text = "\n".join(lines)
        blocks.append(f"==> {name} <==\n{text}" if header else text)
    return Result("\n".join(errors + blocks), ok=not errors)


def _apply_each(names, action):
    """Применяет ``action`` к каждому имени, собирая сообщения об ошибках."""
    errors = []
    for name in names:
        try:
            action(name)
        except CommandError as err:
            errors.append(str(err))
    return Result("\n".join(errors), ok=not errors)


def _touch_one(shell, name):
    """Создаёт пустой файл ``name``, если такого пути ещё нет."""
    parts = normalize(shell.cwd, name)
    if shell.vfs.get(parts) is not None:
        return
    prefix = f"touch: невозможно выполнить touch для '{name}': "
    parent = shell.vfs.get(parts[:-1])
    if parent is None:
        raise CommandError(prefix + NOT_FOUND)
    if not parent.is_dir:
        raise CommandError(prefix + NOT_DIR)
    shell.vfs.add_file(join_path(parts))


def cmd_touch(shell, args):
    """touch файл...: создаёт пустые файлы (существующие не меняет)."""
    _flags, names = _parse_flags(args, "", "touch")
    if not names:
        raise CommandError("touch: пропущен операнд-файл")
    return _apply_each(names, lambda name: _touch_one(shell, name))


def _rm_one(shell, name, flags):
    """Удаляет ``name`` из VFS; при невозможности бросает CommandError."""
    parts = normalize(shell.cwd, name)
    node = shell.vfs.get(parts)
    prefix = f"rm: невозможно удалить '{name}': "
    if node is None:
        if "f" not in flags:
            raise CommandError(prefix + NOT_FOUND)
        return
    if parts == shell.cwd[:len(parts)]:
        raise CommandError(prefix + "это текущая папка или её родитель")
    if node.is_dir and "r" not in flags:
        raise CommandError(prefix + "Это каталог")
    shell.vfs.remove(parts)


def cmd_rm(shell, args):
    """rm [-r] [-f] путь...: удаляет файлы и папки (-r) в памяти."""
    flags, names = _parse_flags(args, "rf", "rm")
    if not names:
        raise CommandError("rm: пропущен операнд")
    return _apply_each(names, lambda name: _rm_one(shell, name, flags))


def cmd_exit(shell, args):
    """exit: завершает работу эмулятора."""
    if args:
        raise CommandError("exit: слишком много аргументов")
    return Result(should_exit=True)


def cmd_vfs_info(shell, args):
    """vfs-info: служебная команда, показывает источник и дерево VFS."""
    if args:
        raise CommandError("vfs-info: аргументы не поддерживаются")
    return Result(f"VFS: {shell.vfs.source}\n{shell.vfs.tree()}")


COMMANDS = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "history": cmd_history,
    "who": cmd_who,
    "head": cmd_head,
    "touch": cmd_touch,
    "rm": cmd_rm,
    "exit": cmd_exit,
    "vfs-info": cmd_vfs_info,
}
