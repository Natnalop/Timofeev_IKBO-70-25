"""Загрузка и проверка тестовых репозиториев JSON."""

import json
import re
from pathlib import Path
from urllib.request import urlopen

from .index import download_index
from .models import TEST_PACKAGE_PATTERN, VERSION_PATTERN, AppError, Package
from .repository import Repository


def valid_test_dependency(value):
    """Проверить заглавное латинское имя зависимости тестового пакета."""
    return isinstance(value, str) and re.fullmatch(TEST_PACKAGE_PATTERN, value)


def validate_record(name, record):
    """Проверить поля одной записи тестового пакета."""
    if not valid_test_dependency(name) or not isinstance(record, dict):
        raise AppError("JSON: имена пакетов должны состоять из A-Z")
    if set(record) != {"version", "dependencies"}:
        raise AppError(f"JSON: неверная запись {name}")
    version = record["version"]
    if not isinstance(version, str):
        raise AppError(f"JSON: неверная запись {name}")
    if not re.fullmatch(VERSION_PATTERN, version):
        raise AppError(f"JSON: неверная запись {name}")
    dependencies = record["dependencies"]
    if not isinstance(dependencies, list):
        raise AppError(f"JSON: неверные зависимости {name}")
    if not all(valid_test_dependency(value) for value in dependencies):
        raise AppError(f"JSON: неверные зависимости {name}")
    return Package(name, version, tuple(dependencies))


def load_test_repository(path):
    """Прочитать JSON и убедиться, что все ссылки на пакеты существуют."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AppError(f"JSON: {exc}") from exc
    if not isinstance(data, dict) or not data:
        raise AppError("JSON: требуется непустой объект пакетов")
    repo = Repository(
        validate_record(name, record) for name, record in data.items()
    )
    for package in repo.packages:
        repo.dependencies(package)
    return repo


def load_repository(config, fetcher=urlopen):
    """Выбрать чтение JSON или загрузку реального репозитория Alpine."""
    if config.test_mode:
        return load_test_repository(config.repository)
    return download_index(config.repository, fetcher)
