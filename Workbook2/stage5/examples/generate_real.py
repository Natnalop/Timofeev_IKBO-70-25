"""Воспроизводимые D2-примеры из текстового снимка официального индекса."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import depgraph as graph  # noqa: E402


def find_d2(parser):
    """Найти установленный D2 или сообщить, где доступны готовые SVG."""
    local = HERE.parents[1] / ".tools/d2.exe"
    command = str(local) if local.is_file() else shutil.which("d2")
    if not command:
        parser.error(
            "Для создания SVG нужен D2 в PATH или Workbook2/.tools/d2.exe. "
            "Готовые SVG уже находятся в examples."
        )
    return command


def save_config(config, path):
    """Записать пользовательские параметры примера в TOML."""
    lines = [
        f"{key} = {json.dumps(value)}" for key, value in vars(config).items()
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_package(repo, name, metadata, d2_command):
    """Сформировать один D2-граф и вызвать внешний D2 для отрисовки."""
    package = repo.names[name][-1]
    config = graph.Config(name, metadata["url"], False, package.version, 20, "")
    nodes, edges = graph.build_graph(repo, package, config)
    d2_path, svg_path = HERE / f"{name}.d2", HERE / f"{name}.svg"
    d2_path.write_text(graph.to_d2(nodes, edges), encoding="utf-8")
    subprocess.run([d2_command, str(d2_path), str(svg_path)], check=True)
    save_config(config, HERE / f"{name}.toml")
    return {
        "version": package.version,
        "nodes": len(nodes),
        "edges": len(edges),
    }


def main():
    """Пересоздать три реальных графа из сохраненного текстового индекса."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    command = find_d2(parser)
    repo = graph.parse_index((HERE / "APKINDEX.txt").read_text("utf-8"))
    metadata = json.loads((HERE / "snapshot.json").read_text("utf-8"))
    for name in metadata["packages"]:
        metadata["packages"][name] = render_package(
            repo, name, metadata, command
        )
    path = HERE / "snapshot.json"
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
