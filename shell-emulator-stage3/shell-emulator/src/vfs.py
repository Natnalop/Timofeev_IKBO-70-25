"""Виртуальная файловая система (VFS), целиком хранящаяся в памяти.

Источник VFS - ZIP-архив. Архив читается через ``zipfile`` прямо в память,
на диск ничего не распаковывается. Содержимое файлов хранится как bytes,
двоичные данные при выводе представляются в формате base64.
"""
import base64
import os
import zipfile

DEFAULT_SOURCE = "<по умолчанию, в памяти>"
INDENT = "  "
PNG_PIXEL_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4"
    "z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg=="
)


class VFSError(Exception):
    """Ошибка загрузки или работы с VFS."""


class Node:
    """Узел дерева: файл (с данными) или папка (с потомками)."""

    def __init__(self, name, is_dir, data=b""):
        """Создаёт узел с именем ``name``."""
        self.name = name
        self.is_dir = is_dir
        self.data = data
        self.children = {} if is_dir else None

    def is_binary(self):
        """Возвращает True, если данные не являются текстом UTF-8."""
        try:
            self.data.decode("utf-8")
        except UnicodeDecodeError:
            return True
        return False

    def as_text(self):
        """Возвращает текст файла или base64-строку для двоичных данных."""
        if self.is_binary():
            encoded = base64.b64encode(self.data).decode("ascii")
            return "base64:" + encoded
        return self.data.decode("utf-8")


def split_path(path):
    """Разбивает путь на непустые части."""
    return [part for part in path.split("/") if part]


def _walk(node, indent, lines):
    """Дописывает в ``lines`` строки дерева для потомков ``node``."""
    for name in sorted(node.children):
        child = node.children[name]
        if child.is_dir:
            lines.append(f"{indent}{name}/")
            _walk(child, indent + INDENT, lines)
        else:
            kind = "bin" if child.is_binary() else "txt"
            size = len(child.data)
            lines.append(f"{indent}{name}  ({size} байт, {kind})")


def _load_entries(vfs, archive):
    """Читает все записи ZIP-архива в память VFS."""
    for info in archive.infolist():
        name = info.filename.replace("\\", "/")
        if ".." in split_path(name):
            raise VFSError(f"небезопасный путь в архиве: {name}")
        if info.is_dir():
            vfs.add_dir(name)
        else:
            vfs.add_file(name, archive.read(info))


class VFS:
    """Виртуальная файловая система в памяти."""

    def __init__(self):
        """Создаёт пустую VFS с корневой папкой."""
        self.root = Node("", True)
        self.source = DEFAULT_SOURCE

    def _make_dir(self, parts):
        """Возвращает папку по частям пути, создавая недостающие."""
        node = self.root
        for part in parts:
            child = node.children.get(part)
            if child is None:
                child = Node(part, True)
                node.children[part] = child
            elif not child.is_dir:
                raise VFSError(f"'{part}' - файл, а не папка")
            node = child
        return node

    def add_dir(self, path):
        """Создаёт папку (и все родительские) по пути ``path``."""
        self._make_dir(split_path(path))

    def add_file(self, path, data=b""):
        """Создаёт файл с содержимым ``data`` по пути ``path``."""
        parts = split_path(path)
        if not parts:
            raise VFSError("пустой путь")
        parent = self._make_dir(parts[:-1])
        parent.children[parts[-1]] = Node(parts[-1], False, data)

    @classmethod
    def default(cls):
        """Создаёт VFS по умолчанию (когда путь к архиву не указан)."""
        vfs = cls()
        vfs.add_dir("home/user")
        text = "Это VFS по умолчанию.\nОна живёт только в памяти.\n"
        vfs.add_file("home/user/readme.txt", text.encode("utf-8"))
        pixel = base64.b64decode(PNG_PIXEL_B64)
        vfs.add_file("home/user/pixel.png", pixel)
        vfs.add_dir("tmp")
        return vfs

    @classmethod
    def from_zip(cls, path):
        """Загружает VFS из ZIP-архива, ничего не распаковывая на диск."""
        if not os.path.exists(path):
            raise VFSError(f"файл VFS не найден: {path}")
        if not os.path.isfile(path):
            raise VFSError(f"путь VFS не является файлом: {path}")
        vfs = cls()
        vfs.source = path
        try:
            with zipfile.ZipFile(path) as archive:
                _load_entries(vfs, archive)
        except zipfile.BadZipFile:
            raise VFSError(f"неверный формат VFS (не ZIP-архив): {path}")
        except (RuntimeError, NotImplementedError) as err:
            raise VFSError(f"не удалось прочитать архив ({err}): {path}")
        except OSError as err:
            raise VFSError(f"ошибка чтения VFS: {err}")
        return vfs

    def tree(self):
        """Возвращает текстовое дерево VFS для команды ``vfs-info``."""
        lines = ["/"]
        _walk(self.root, INDENT, lines)
        return "\n".join(lines)
