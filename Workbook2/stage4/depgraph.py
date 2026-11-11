"""Совместимая точка входа этапа 4; реализация находится в src."""

import sys
from pathlib import Path
from urllib.request import urlopen

STAGE = 4
FOLDER = Path(__file__).resolve().parent
sys.path.insert(0, str(FOLDER / "src"))

from apkgraph4 import (  # noqa: E402
    AppError,
    Config,
    Package,
    Repository,
    bfs_recursive,
    build_graph,
    load_config,
    parse_index,
    satisfies,
    split_dependency,
    to_d2,
    version_key,
)
from apkgraph4.cli import main as run_cli  # noqa: E402
from apkgraph4.fixtures import (  # noqa: E402
    load_repository as read_repository,
)

__all__ = [
    "AppError",
    "Config",
    "Package",
    "Repository",
    "bfs_recursive",
    "build_graph",
    "load_config",
    "load_repository",
    "main",
    "parse_index",
    "satisfies",
    "split_dependency",
    "to_d2",
    "urlopen",
    "version_key",
]


def load_repository(config):
    """Сохранить прежний API и возможность подменять HTTP в тестах."""
    return read_repository(config, fetcher=urlopen)


def main(argv=None):
    """Запустить модульный CLI этапа с прежней командой запуска."""
    return run_cli(STAGE, FOLDER, argv)


if __name__ == "__main__":
    sys.exit(main())
