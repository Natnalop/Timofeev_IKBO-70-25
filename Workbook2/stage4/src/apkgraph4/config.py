"""Чтение TOML и проверка пользовательских параметров."""

import re
import tomllib
from pathlib import Path
from urllib.parse import urlparse

from .models import (
    CONTROL_LIMIT,
    MAX_DEPTH,
    PACKAGE_PATTERN,
    TEST_PACKAGE_PATTERN,
    VERSION_PATTERN,
    AppError,
    Config,
)

PARAMETER_TYPES = {
    "package": str,
    "repository": str,
    "test_mode": bool,
    "version": str,
    "max_depth": int,
    "filter_substring": str,
}


def read_toml(path):
    """Прочитать TOML и преобразовать ошибки чтения в ошибки приложения."""
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise AppError(f"TOML: {exc}") from exc


def validate_schema(data):
    """Проверить наличие, типы и отсутствие неизвестных параметров."""
    errors = []
    for key, kind in PARAMETER_TYPES.items():
        if key not in data or type(data[key]) is not kind:
            errors.append(f"{key}: требуется {kind.__name__}")
    unknown = data.keys() - PARAMETER_TYPES.keys()
    errors.extend(f"{key}: неизвестный параметр" for key in sorted(unknown))
    if errors:
        raise AppError("; ".join(errors))


def validate_identity(data):
    """Проверить синтаксис имени и версии корневого пакета."""
    errors = []
    pattern = TEST_PACKAGE_PATTERN if data["test_mode"] else PACKAGE_PATTERN
    if not re.fullmatch(pattern, data["package"]):
        errors.append("package: недопустимое имя пакета")
    if not re.fullmatch(VERSION_PATTERN, data["version"]):
        errors.append(
            "version: требуется непустая версия, начинающаяся с цифры"
        )
    return errors


def validate_analysis(data):
    """Проверить глубину и подстроку исключения пакетов."""
    errors = []
    if not 0 <= data["max_depth"] <= MAX_DEPTH:
        errors.append(f"max_depth: допустимо целое число от 0 до {MAX_DEPTH}")
    excluded = data["filter_substring"]
    if any(ord(character) < CONTROL_LIMIT for character in excluded):
        errors.append("filter_substring: управляющие символы запрещены")
    if excluded and excluded in data["package"]:
        errors.append("filter_substring: фильтр исключает корневой пакет")
    return errors


def valid_repository_url(value):
    """Проверить HTTP(S) URL, включая синтаксис адреса и порта."""
    try:
        parsed = urlparse(value)
        _ = parsed.port
    except ValueError:
        return False
    return bool(
        parsed.scheme in ("http", "https")
        and parsed.hostname
        and not parsed.query
        and not parsed.fragment
    )


def validate_repository(data, config_path):
    """Разрешить локальный путь либо проверить URL реального индекса."""
    if not data["test_mode"]:
        if valid_repository_url(data["repository"]):
            return []
        return [
            "repository: требуется HTTP(S) URL каталога архитектуры "
            "или APKINDEX.tar.gz"
        ]
    local = Path(data["repository"])
    if not local.is_absolute():
        local = config_path.resolve().parent / local
    data["repository"] = str(local)
    if not local.is_file():
        return ["repository: файл тестового репозитория не найден"]
    return []


def load_config(path):
    """Прочитать и проверить все шесть параметров TOML-конфигурации."""
    data = read_toml(Path(path))
    validate_schema(data)
    errors = validate_identity(data)
    errors.extend(validate_analysis(data))
    errors.extend(validate_repository(data, Path(path)))
    if errors:
        raise AppError("; ".join(errors))
    return Config(**data)
