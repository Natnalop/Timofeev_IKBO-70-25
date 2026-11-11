"""Рисование графа в SVG средствами стандартной библиотеки Python."""
from collections import defaultdict
from html import escape


def to_svg(nodes, edges):
    nodes, edges = sorted(nodes), sorted(edges)
    incoming = {node: 0 for node in nodes}
    outgoing = defaultdict(list)
    for source, target in edges:
        incoming[target] += 1
        outgoing[source].append(target)
    # Слои по самому длинному пути в ациклической части графа.
    levels = dict.fromkeys(nodes, 0)
    frontier = sorted(node for node in nodes if incoming[node] == 0)
    processed = set()
    while frontier:
        source = frontier.pop(0)
        processed.add(source)
        for target in outgoing[source]:
            levels[target] = max(levels[target], levels[source] + 1)
            incoming[target] -= 1
            if incoming[target] == 0:
                frontier.append(target)
                frontier.sort()
    # Циклическую часть размещаем отдельными колонками, без рекурсии.
    next_level = max((levels[n] for n in processed), default=-1) + 1
    for node in nodes:
        if node not in processed:
            levels[node] = next_level
            next_level += 1
    layers = defaultdict(list)
    for node in nodes:
        layers[levels[node]].append(node)
    box_width = max(180, max((len(n.name) * 9 + 30 for n in nodes), default=180))
    box_height, row_gap, column_gap, margin = 66, 48, 130, 40
    height = max((len(group) for group in layers.values()), default=1) * (box_height + row_gap) + 2 * margin
    width = (max(layers, default=0) + 1) * (box_width + column_gap) - column_gap + 2 * margin
    positions = {}
    for level, group in sorted(layers.items()):
        group_height = len(group) * (box_height + row_gap) - row_gap
        for row, node in enumerate(group):
            positions[node] = (margin + level * (box_width + column_gap),
                               (height - group_height) / 2 + row * (box_height + row_gap))
    # Длинные и обратные ребра проходят по отдельным полосам снизу.
    detours = [(a, b) for a, b in edges if levels[b] != levels[a] + 1]
    bottom = height
    height += len(detours) * 16 + (30 if detours else 0)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">',
             '<title>Граф зависимостей пакетов</title>',
             f'<rect width="{width}" height="{height}" fill="white"/>',
             '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L8,4 L0,8 Z" fill="black"/></marker></defs>']
    lane = 0
    for index, (source, target) in enumerate(edges):
        sx, sy = positions[source]
        tx, ty = positions[target]
        start_x, start_y = sx + box_width, sy + box_height / 2
        end_x, end_y = tx, ty + box_height / 2
        if (source, target) in detours:
            lane_y = bottom + lane * 16
            lane += 1
            # Каналы расположены в свободных промежутках между колонками.
            exit_x = start_x + 16 + (index % 5) * 8
            entry_x = end_x - 16 - (index % 5) * 8
            points = [(start_x, start_y), (exit_x, start_y), (exit_x, lane_y),
                      (entry_x, lane_y), (entry_x, end_y), (end_x, end_y)]
        else:
            channel_x = start_x + 24 + (index % 7) * 12
            points = [(start_x, start_y), (channel_x, start_y),
                      (channel_x, end_y), (end_x, end_y)]
        coordinates = ' '.join(f'{x:g},{y:g}' for x, y in points)
        parts.append(f'<polyline points="{coordinates}" fill="none" stroke="black" stroke-width="1.2" marker-end="url(#arrow)"/>')
    # Узлы поверх линий; подписи всегда остаются на белом фоне.
    for node in nodes:
        x, y = positions[node]
        parts.append(f'<rect x="{x:g}" y="{y:g}" width="{box_width}" height="{box_height}" fill="white" stroke="black"/>')
        parts.append(f'<text x="{x + box_width / 2:g}" y="{y + 26:g}" text-anchor="middle" fill="black" font-family="Arial, sans-serif" font-size="16">{escape(node.name)}</text>')
        parts.append(f'<text x="{x + box_width / 2:g}" y="{y + 48:g}" text-anchor="middle" fill="black" font-family="Arial, sans-serif" font-size="14">{escape(node.version)}</text>')
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'
