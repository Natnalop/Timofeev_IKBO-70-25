"""Проверки самостоятельного запуска четвертого этапа."""

import os
import subprocess
import sys
import unittest
from pathlib import Path

STAGE_FOLDER = Path(__file__).resolve().parents[1]


def run_stage(*arguments):
    """Вызвать CLI этапа 4 с фиксированной кодировкой вывода."""
    command = [sys.executable, str(STAGE_FOLDER / "depgraph.py")]
    return subprocess.run(
        [*command, *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ | {"PYTHONIOENCODING": "utf-8"},
    )


class ReverseCliTests(unittest.TestCase):
    """Проверки направления и максимальной глубины обратного обхода."""

    def test_reverse_depth_one(self):
        """На первом обратном уровне A зависит только от D по обходу."""
        config = STAGE_FOLDER / "examples/depth1.toml"
        result = run_stage("--config", str(config), "--reverse")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("A@1.0 -> D@1.0", result.stdout)
        self.assertNotIn("B@1.0", result.stdout)

    def test_reverse_isolated(self):
        """Изолированная вершина не получает ложных обратных зависимостей."""
        config = STAGE_FOLDER / "examples/isolated.toml"
        result = run_stage("--config", str(config), "--reverse")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(" -> ", result.stdout)
