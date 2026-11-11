"""Командный интерфейс отдельного этапа проектной работы."""

import argparse
import sys
from pathlib import Path

from .config import load_config
from .diagrams import to_d2
from .fixtures import load_repository
from .graph import build_graph
from .models import AppError

REVERSE_STAGE = 4
DIAGRAM_STAGE = 5


def make_parser(stage, folder):
    """Создать CLI с TOML-конфигурацией и режимами текущего этапа."""
    parser = argparse.ArgumentParser(
        description=f"APK dependency graph, этап {stage}"
    )
    parser.add_argument("--config", type=Path, default=folder / "config.toml")
    if stage == REVERSE_STAGE:
        parser.add_argument(
            "--reverse",
            action="store_true",
            help="обратные транзитивные зависимости",
        )
    return parser


def execute(args, stage):
    """Загрузить данные и вывести граф в формате текущего этапа."""
    config = load_config(args.config)
    repo = load_repository(config)
    root = repo.root(config.package, config.version)
    nodes, edges = build_graph(
        repo, root, config, getattr(args, "reverse", False)
    )
    if stage == DIAGRAM_STAGE:
        print(to_d2(nodes, edges), end="")
        return
    print("Узлы: " + ", ".join(package.key for package in sorted(nodes)))
    for source, target in sorted(edges):
        print(f"{source.key} -> {target.key}")


def main(stage, folder, argv=None):
    """Выполнить приложение и вернуть стандартный код завершения."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = make_parser(stage, folder).parse_args(argv)
    try:
        execute(args, stage)
    except (AppError, RecursionError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2
    return 0
