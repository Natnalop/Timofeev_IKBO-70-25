"""Детерминированное текстовое представление графа на языке D2."""

import json

D2_HEADER = (
    "direction: right",
    "vars: {",
    "  d2-config: {",
    "    layout-engine: elk",
    "  }",
    "}",
    "style.fill: white",
)
NODE_STYLE = (
    "  shape: rectangle",
    "  style.fill: white",
    "  style.stroke: black",
    "  style.font-color: black",
    "  style.stroke-width: 1",
    "  style.border-radius: 0",
    "  style.shadow: false",
    "  style.font-size: 18",
    "}",
)
EDGE_STYLE = (
    "  style.stroke: black",
    "  style.stroke-width: 1",
    "  style.border-radius: 0",
    "}",
)


def quote(value):
    """Экранировать подпись либо идентификатор для синтаксиса D2."""
    return json.dumps(value, ensure_ascii=False)


def to_d2(nodes, edges):
    """Сформировать черно-белую диаграмму с раскладкой ELK."""
    lines = list(D2_HEADER)
    for package in sorted(nodes):
        label = quote(f"{package.name}\n{package.version}")
        lines.append(f"{quote(package.key)}: {label} {{")
        lines.extend(NODE_STYLE)
    for source, target in sorted(edges):
        lines.append(f"{quote(source.key)} -> {quote(target.key)} {{")
        lines.extend(EDGE_STYLE)
    return "\n".join(lines) + "\n"
