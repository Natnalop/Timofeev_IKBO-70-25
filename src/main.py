"""Выбор самостоятельного CLI этапа 4 или 5 из корня репозитория."""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STAGE = 5
AVAILABLE_STAGES = (4, 5)


def main(argv=None):
    """Передать аргументы выбранному этапу с правильным путем запуска."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", type=int, choices=AVAILABLE_STAGES, default=DEFAULT_STAGE
    )
    args, remaining = parser.parse_known_args(argv)
    entry = ROOT / "Workbook2" / f"stage{args.stage}" / "depgraph.py"
    result = subprocess.run([sys.executable, str(entry), *remaining])
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
