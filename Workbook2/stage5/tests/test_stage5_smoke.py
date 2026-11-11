"""Проверки самостоятельного запуска пятого этапа."""

import os
import subprocess
import sys
import unittest
from pathlib import Path

STAGE_FOLDER = Path(__file__).resolve().parents[1]


def run_stage(*arguments):
    """Вызвать CLI этапа 5 с фиксированной кодировкой вывода."""
    command = [sys.executable, str(STAGE_FOLDER / "depgraph.py")]
    return subprocess.run(
        [*command, *arguments],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ | {"PYTHONIOENCODING": "utf-8"},
    )


class DiagramCliTests(unittest.TestCase):
    """Проверки D2-вывода и изолированных вершин без внешнего рендера."""

    def test_cycle_outputs_all_edges(self):
        """Ромб и цикл сохраняют все шесть ребер тестового репозитория."""
        result = run_stage()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count(" -> "), 6)
        self.assertIn("layout-engine: elk", result.stdout)

    def test_isolated_vertex(self):
        """Изолированный пакет получает подпись без лишних ребер."""
        config = STAGE_FOLDER / "examples/isolated.toml"
        result = run_stage("--config", str(config))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"Z@1.0"', result.stdout)
        self.assertNotIn(" -> ", result.stdout)
