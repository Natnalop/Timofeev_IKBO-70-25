"""Ядро эмулятора: парсер, команды, выполнение стартового скрипта.

Модуль не зависит от GUI, поэтому его можно тестировать без окна.
"""
import getpass
import os
import re
import shlex
import socket
from dataclasses import dataclass

from vfs import VFS

ENV_RE = re.compile(r"\$(\w+)|\$\{(\w+)\}")
MAX_CD_ARGS = 1


def get_user():
    """Возвращает имя пользователя реальной ОС."""
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return "user"


def get_host():
    """Возвращает имя хоста реальной ОС."""
    return socket.gethostname() or "localhost"


def _env_value(match):
    """Возвращает значение переменной окружения для совпадения."""
    name = match.group(1) or match.group(2)
    value = os.environ.get(name)
    if value is None and name == "HOME":
        value = os.path.expanduser("~")
    return value or ""


def expand_env(text):
    """Раскрывает переменные окружения вида ``$HOME`` и ``${HOME}``."""
    return ENV_RE.sub(_env_value, text)


class ParseError(Exception):
    """Ошибка разбора введённой строки."""


def parse(line):
    """Разбивает строку на токены с раскрытием переменных и кавычек."""
    try:
        return shlex.split(expand_env(line))
    except ValueError as err:
        raise ParseError(f"ошибка разбора: {err}")


@dataclass
class Result:
    """Результат выполнения команды."""

    out: str = ""
    ok: bool = True
    should_exit: bool = False


class Shell:
    """Интерпретатор команд эмулятора."""

    def __init__(self, vfs=None, prompt=None):
        """Создаёт оболочку с VFS ``vfs`` и приглашением ``prompt``."""
        self.vfs = VFS.default() if vfs is None else vfs
        self.user = get_user()
        self.host = get_host()
        default_prompt = f"[{self.user}@{self.host}]$ "
        self.prompt = default_prompt if prompt is None else prompt
        self.commands = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "exit": self.cmd_exit,
            "vfs-info": self.cmd_vfs_info,
        }

    def run(self, line):
        """Выполняет одну строку ввода и возвращает ``Result``."""
        if not line.strip():
            return Result()
        try:
            tokens = parse(line)
        except ParseError as err:
            return Result(f"эмулятор: {err}", ok=False)
        if not tokens:
            return Result()
        name, args = tokens[0], tokens[1:]
        handler = self.commands.get(name)
        if handler is None:
            return Result(f"{name}: команда не найдена", ok=False)
        return handler(args)

    def run_script(self, path, write):
        """Выполняет стартовый скрипт, показывая ввод и вывод.

        Ошибочные строки пропускаются. Возвращает True, если в скрипте
        была выполнена команда ``exit``.
        """
        try:
            with open(path, encoding="utf-8-sig") as file:
                lines = file.read().splitlines()
        except OSError as err:
            write(f"[скрипт] ошибка: не удалось открыть '{path}': {err}")
            return False
        for number, line in enumerate(lines, 1):
            if self._run_script_line(number, line, write):
                return True
        return False

    def _run_script_line(self, number, line, write):
        """Выполняет строку скрипта; True, если выполнен ``exit``."""
        if not line.strip():
            return False
        if line.lstrip().startswith("#"):
            write(line)
            return False
        write(self.prompt + line)
        result = self.run(line)
        if result.out:
            write(result.out)
        if not result.ok:
            write(f"[скрипт] ошибка в строке {number}, строка пропущена")
        return result.should_exit

    def cmd_ls(self, args):
        """Заглушка ``ls``: печатает имя и аргументы (логика - этап 4)."""
        return Result(" ".join(["ls"] + args))

    def cmd_cd(self, args):
        """Заглушка ``cd``: печатает имя и аргументы (логика - этап 4)."""
        if len(args) > MAX_CD_ARGS:
            return Result("cd: слишком много аргументов", ok=False)
        return Result(" ".join(["cd"] + args))

    def cmd_exit(self, args):
        """Команда ``exit``: завершает работу эмулятора."""
        if args:
            return Result("exit: слишком много аргументов", ok=False)
        return Result(should_exit=True)

    def cmd_vfs_info(self, args):
        """Служебная команда: показывает источник и дерево VFS."""
        if args:
            return Result("vfs-info: аргументы не поддерживаются", ok=False)
        return Result(f"VFS: {self.vfs.source}\n{self.vfs.tree()}")
