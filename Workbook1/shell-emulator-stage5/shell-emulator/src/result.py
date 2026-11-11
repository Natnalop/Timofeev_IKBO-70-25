"""Результат выполнения команды и ошибка команды."""
from dataclasses import dataclass


@dataclass
class Result:
    """Результат выполнения команды."""

    out: str = ""
    ok: bool = True
    should_exit: bool = False


class CommandError(Exception):
    """Ошибка выполнения команды с готовым текстом сообщения."""
