"""Локальная проверка структуры и размеров кода этапов 4 и 5."""

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_FILE_LINES = 1000
MAX_LINE_LENGTH = 80
MAX_FUNCTION_LINES = 40
MAX_ARGUMENTS = 7
FOLDERS = (
    "Workbook2/stage4",
    "Workbook2/stage5",
    "Workbook2/tests",
    "src",
    "tests",
    "Workbook2/tools",
)
EXTRA_FILES = ("Workbook2/build_stages.py", "Workbook2/prepare_examples.py")
REQUIRED = ("README.md", ".gitignore", "src", "tests", "run.bat")


def argument_count(node):
    """Посчитать явные аргументы функции, включая именованные."""
    arguments = node.args
    return sum(
        map(len, (arguments.posonlyargs, arguments.args, arguments.kwonlyargs))
    )


def measure_file(path):
    """Измерить размер файла, строки, функции и их аргументы."""
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    functions = [
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    ]
    documented = (ast.Module, ast.ClassDef, ast.FunctionDef)
    missing = [
        node.lineno if hasattr(node, "lineno") else 1
        for node in ast.walk(tree)
        if isinstance(node, documented) and not ast.get_docstring(node)
    ]
    return {
        "file": str(path.relative_to(ROOT)),
        "file_lines": len(text.splitlines()),
        "line_length": max(map(len, text.splitlines()), default=0),
        "function_lines": max(
            (node.end_lineno - node.lineno + 1 for node in functions),
            default=0,
        ),
        "arguments": max(map(argument_count, functions), default=0),
        "missing_docstrings": missing,
    }


def violates_limits(metrics):
    """Проверить метрики файла по порогам из перечня преподавателя."""
    return any(
        (
            metrics["file_lines"] > MAX_FILE_LINES,
            metrics["line_length"] > MAX_LINE_LENGTH,
            metrics["function_lines"] > MAX_FUNCTION_LINES,
            metrics["arguments"] > MAX_ARGUMENTS,
            bool(metrics["missing_docstrings"]),
        )
    )


def inspect_structure():
    """Проверить корень репозитория и структуру двух последних этапов."""
    folders = (ROOT, ROOT / "Workbook2/stage4", ROOT / "Workbook2/stage5")
    return [
        str(folder / item)
        for folder in folders
        for item in REQUIRED
        if not (folder / item).exists()
    ]


def main():
    """Вывести воспроизводимый отчет; сложность проверяется отдельно."""
    files = [ROOT / relative for relative in EXTRA_FILES]
    for relative in FOLDERS:
        files.extend((ROOT / relative).rglob("*.py"))
    metrics = [measure_file(path) for path in sorted(set(files))]
    failures = [item for item in metrics if violates_limits(item)]
    missing = inspect_structure()
    report = {
        "scope": list(FOLDERS),
        "files_checked": len(metrics),
        "missing_structure": missing,
        "failures": failures,
        "max_line_length": max(item["line_length"] for item in metrics),
        "max_function_lines": max(item["function_lines"] for item in metrics),
        "max_arguments": max(item["arguments"] for item in metrics),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return int(bool(failures or missing))


if __name__ == "__main__":
    sys.exit(main())
