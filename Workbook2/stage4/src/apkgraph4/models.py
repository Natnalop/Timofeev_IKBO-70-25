"""Модели данных и общие ограничения приложения."""

from dataclasses import dataclass

MAX_DEPTH = 200
CONTROL_LIMIT = 32
MAX_BYTES = 32 * 1024 * 1024
NETWORK_TIMEOUT = 30
FIELD_PREFIX_SIZE = 2
FIELD_SEPARATOR_INDEX = 1
VERSION_PATTERN = r"[0-9][a-zA-Z0-9._+-]*"
PACKAGE_PATTERN = r"[a-zA-Z0-9][a-zA-Z0-9+_.-]*"
TEST_PACKAGE_PATTERN = r"[A-Z]+"


class AppError(ValueError):
    """Ожидаемая ошибка конфигурации или данных репозитория."""


@dataclass(frozen=True)
class Config:
    """Шесть пользовательских параметров анализа зависимостей."""

    package: str
    repository: str
    test_mode: bool
    version: str
    max_depth: int
    filter_substring: str


@dataclass(frozen=True, order=True)
class Package:
    """Запись пакета, его зависимостей и виртуальных имен."""

    name: str
    version: str
    dependencies: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()

    @property
    def key(self):
        """Вернуть устойчивый идентификатор вершины графа."""
        return f"{self.name}@{self.version}"
