"""Общая точка запуска проверок проектной работы из корня репозитория."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_FOLDERS = (
    "Workbook2/tests",
    "Workbook2/stage4/tests",
    "Workbook2/stage5/tests",
)


def load_tests(loader, standard_tests, pattern):
    """Собрать проверки логики и самостоятельных CLI этапов 4 и 5."""
    suite = unittest.TestSuite()
    for relative in TEST_FOLDERS:
        folder = str(ROOT / relative)
        suite.addTests(loader.discover(folder, top_level_dir=folder))
    return suite
