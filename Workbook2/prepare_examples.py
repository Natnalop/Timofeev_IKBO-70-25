"""Создать конфигурации и протоколы, сохранив документацию этапов."""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GRAPH = {
    "A": ["B", "C"],
    "B": ["D"],
    "C": ["D", "E"],
    "D": ["A"],
    "E": [],
    "Z": [],
}
CASES = {
    "cycle": {},
    "depth1": {"depth": 1},
    "depth0": {"depth": 0},
    "filter": {"excluded": "B"},
    "isolated": {"package": "Z"},
}
INVALID_CASES = {
    "package": {"package": "bad name"},
    "repository": {"repository": "missing.json"},
    "test_mode": {"test": "yes"},
    "version": {"version": ""},
    "max_depth": {"depth": -1},
    "filter_substring": {"excluded": "A"},
}
EARLY_STAGE = 3
REVERSE_STAGE = 4


def config(
    package="A",
    repository="repository.json",
    test=True,
    version="1.0",
    depth=10,
    excluded="",
):
    """Сформировать шесть пользовательских параметров в формате TOML."""
    values = {
        "package": package,
        "repository": repository,
        "test_mode": test,
        "version": version,
        "max_depth": depth,
        "filter_substring": excluded,
    }
    return (
        "\n".join(
            f"{key} = {json.dumps(value, ensure_ascii=False)}"
            for key, value in values.items()
        )
        + "\n"
    )


def run_example(folder, path, reverse=False):
    """Запустить пример отдельным процессом и собрать stdout и stderr."""
    command = [
        sys.executable,
        str(folder / "depgraph.py"),
        "--config",
        str(path),
    ]
    if reverse:
        command.append("--reverse")
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=os.environ | {"PYTHONIOENCODING": "utf-8"},
    )


def write_configs(folder):
    """Сохранить тестовый репозиторий и стандартные конфигурации этапа."""
    folder.mkdir(exist_ok=True)
    repository = {
        name: {"version": "1.0", "dependencies": dependencies}
        for name, dependencies in GRAPH.items()
    }
    (folder / "repository.json").write_text(
        json.dumps(repository, indent=2), encoding="utf-8"
    )
    (folder / "config.toml").write_text(config(), encoding="utf-8")
    examples = folder / "examples"
    examples.mkdir(exist_ok=True)
    for name, values in CASES.items():
        text = config(repository="../repository.json", **values)
        (examples / f"{name}.toml").write_text(text, encoding="utf-8")


def write_transcript(stage, folder):
    """Выполнить нужные случаи и сохранить фактический вывод этапа."""
    transcript = []
    cases = CASES if stage >= EARLY_STAGE else {"cycle": {}}
    directions = (False, True) if stage == REVERSE_STAGE else (False,)
    for name in cases:
        for reverse in directions:
            result = run_example(
                folder, folder / "examples" / f"{name}.toml", reverse
            )
            transcript.append(
                f"CASE {name}, reverse={reverse}, exit={result.returncode}\n"
                + result.stdout
                + result.stderr
            )
    (folder / "examples/demo.txt").write_text(
        "\n".join(transcript), encoding="utf-8"
    )


def write_invalid_examples():
    """Продемонстрировать ошибку каждого параметра на первом этапе."""
    folder = ROOT / "stage1"
    transcript = []
    for name, values in INVALID_CASES.items():
        parameters = {"repository": "../repository.json"} | values
        path = folder / "examples" / f"invalid_{name}.toml"
        path.write_text(config(**parameters), encoding="utf-8")
        result = run_example(folder, path)
        transcript.append(f"{name}: exit={result.returncode}\n{result.stderr}")
    (folder / "examples/errors.txt").write_text(
        "\n".join(transcript), encoding="utf-8"
    )


def main():
    """Обновить учебные примеры пяти этапов без перезаписи README."""
    for stage in range(1, 6):
        folder = ROOT / f"stage{stage}"
        write_configs(folder)
        write_transcript(stage, folder)
    write_invalid_examples()


if __name__ == "__main__":
    main()
