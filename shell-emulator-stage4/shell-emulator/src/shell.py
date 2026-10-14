"""Ядро эмулятора: парсер и оболочка (состояние и выполнение строк).

Модуль не зависит от GUI, поэтому его можно тестировать без окна.
"""
import getpass
import os
import re
import shlex
import socket
from datetime import datetime

from commands import COMMANDS
from result import CommandError, Result
from vfs import VFS, join_path

ENV_RE = re.compile(r"\$(\w+)|\$\{(\w+)\}")


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


class Shell:
    """Оболочка: хранит текущую папку, историю и выполняет команды."""

    def __init__(self, vfs=None, prompt=None):
        """Создаёт оболочку с VFS ``vfs`` и приглашением ``prompt``."""
        self.vfs = VFS.default() if vfs is None else vfs
        self.user = get_user()
        self.host = get_host()
        self.custom_prompt = prompt
        self.cwd = []
        self.history = []
        self.login_time = datetime.now()

    @property
    def prompt(self):
        """Приглашение: заданное пользователем или с текущей папкой."""
        if self.custom_prompt is not None:
            return self.custom_prompt
        return f"[{self.user}@{self.host} {join_path(self.cwd)}]$ "

    def run(self, line):
        """Выполняет одну строку ввода и возвращает ``Result``."""
        if not line.strip():
            return Result()
        self.history.append(line.strip())
        try:
            tokens = parse(line)
        except ParseError as err:
            return Result(f"эмулятор: {err}", ok=False)
        if not tokens:
            return Result()
        return self.dispatch(tokens[0], tokens[1:])

    def dispatch(self, name, args):
        """Вызывает команду ``name``; ошибки команд даёт как ``Result``."""
        handler = COMMANDS.get(name)
        if handler is None:
            return Result(f"{name}: команда не найдена", ok=False)
        try:
            return handler(self, args)
        except CommandError as err:
            return Result(str(err), ok=False)

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
