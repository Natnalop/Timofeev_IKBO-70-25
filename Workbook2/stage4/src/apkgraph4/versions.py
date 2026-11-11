"""Разбор зависимостей и сравнение поддерживаемых версий Alpine."""

import re

from .models import AppError

DEPENDENCY_PATTERN = re.compile(r"([^<>=~\s]+)(<=|>=|=|<|>|~)?([^\s]*)")
SUFFIX_RANKS = {
    "alpha": -4,
    "beta": -3,
    "pre": -2,
    "rc": -1,
    "cvs": 1,
    "svn": 2,
    "git": 3,
    "hg": 4,
    "p": 5,
}


def split_dependency(value):
    """Разделить зависимость на имя, оператор и ограничение версии."""
    match = DEPENDENCY_PATTERN.fullmatch(value)
    if not match:
        raise AppError(f"Некорректная зависимость: {value}")
    name, operator, version = match.groups()
    if operator and not version:
        raise AppError(f"Некорректная зависимость: {value}")
    return name, operator or "", version


def suffix_key(suffix, version):
    """Преобразовать суффикс версии в его числовой приоритет."""
    match = re.fullmatch(r"([a-z]+)(\d*)", suffix)
    if not match or match[1] not in SUFFIX_RANKS:
        raise AppError(f"Неподдерживаемая версия: {version}")
    return SUFFIX_RANKS[match[1]], int(match[2] or 0)


def version_key(version):
    """Получить ключ числовых частей, суффиксов и ревизии версии."""
    main, _, revision = version.partition("-r")
    parts = main.split("_")
    base = tuple(
        (1, int(token)) if token.isdigit() else (0, token)
        for token in re.findall(r"\d+|[a-zA-Z]+", parts[0])
    )
    suffixes = tuple(suffix_key(suffix, version) for suffix in parts[1:])
    return base, suffixes or ((0, 0),), int(revision or 0)


def satisfies(actual, operator, wanted):
    """Проверить версию по оператору зависимости выбранного пакета."""
    if not operator:
        return True
    if operator == "=":
        return actual == wanted
    if operator == "~":
        return any(
            (
                actual == wanted,
                actual.startswith(wanted + "."),
                actual.startswith(wanted + "-r"),
            )
        )
    left, right = version_key(actual), version_key(wanted)
    comparisons = {
        "<": left < right,
        ">": left > right,
        "<=": left <= right,
        ">=": left >= right,
    }
    return comparisons[operator]
