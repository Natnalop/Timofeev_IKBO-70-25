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
    # Длинные связи разбиваем временными точками в каждом промежуточном слое.
    # Они занимают свободное место между узлами, поэтому связи не уходят под граф.
    node_ids = {node: i for i, node in enumerate(nodes)}
    ranks = {node_ids[node]: levels[node] for node in nodes}
    chains, links = {}, []
    next_id = len(nodes)
    for source, target in edges:
        chain = [node_ids[source]]
        if levels[target] > levels[source]:
            for level in range(levels[source] + 1, levels[target]):
                ranks[next_id] = level
                chain.append(next_id)
                next_id += 1
        chain.append(node_ids[target])
        chains[source, target] = chain
        if levels[target] > levels[source]:
            links.extend(zip(chain, chain[1:]))
    layers = defaultdict(list)
    for item, rank in ranks.items():
        layers[rank].append(item)
    before, after = defaultdict(list), defaultdict(list)
    for left, right in links:
        after[left].append(right)
        before[right].append(left)
    # Сортировка по средней позиции соседей уменьшает пересечения связей.
    for sweep in range(12):
        order = {item: row for group in layers.values() for row, item in enumerate(group)}
        forward = sweep % 2 == 0
        for rank in sorted(layers, reverse=not forward):
            neighbors = before if forward else after
            def center(item):
                rows = sorted(order[n] for n in neighbors[item])
                return sum(rows) / len(rows) if rows else order[item]
            layers[rank].sort(key=lambda item: (center(item), order[item]))
            order.update({item: row for row, item in enumerate(layers[rank])})
    box_width = max(180, max((len(n.name) * 9 + 30 for n in nodes), default=180))
    box_height, row_gap, column_gap, margin = 66, 24, 110, 40
    backward = [(a, b) for a, b in edges if levels[b] <= levels[a]]
    top = margin + len(backward) * 18
    height = max((len(group) for group in layers.values()), default=1) * (box_height + row_gap) + top + margin
    width = (max(layers, default=0) + 1) * (box_width + column_gap) - column_gap + 2 * margin
    centers = {}
    for level, group in sorted(layers.items()):
        group_height = len(group) * (box_height + row_gap) - row_gap
        for row, item in enumerate(group):
            centers[item] = (margin + level * (box_width + column_gap) + box_width / 2,
                             top + (height - top - margin - group_height) / 2 + row * (box_height + row_gap) + box_height / 2)
    positions = {node: (centers[node_ids[node]][0] - box_width / 2,
                        centers[node_ids[node]][1] - box_height / 2) for node in nodes}
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">',
             '<title>Граф зависимостей пакетов</title>',
             f'<rect width="{width}" height="{height}" fill="white"/>',
             '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L8,4 L0,8 Z" fill="black"/></marker></defs>']
    incoming_edges, outgoing_edges = defaultdict(list), defaultdict(list)
    for edge in edges:
        outgoing_edges[edge[0]].append(edge)
        incoming_edges[edge[1]].append(edge)
    for node in nodes:
        outgoing_edges[node].sort(key=lambda edge: centers[chains[edge][1]][1])
        incoming_edges[node].sort(key=lambda edge: centers[chains[edge][-2]][1])
    def port(node, edge, outgoing_port):
        group = outgoing_edges[node] if outgoing_port else incoming_edges[node]
        return positions[node][1] + box_height * (group.index(edge) + 1) / (len(group) + 1)
    gap_links = defaultdict(list)
    for left, right in links:
        gap_links[ranks[left]].append((left, right))
    for group in gap_links.values():
        group.sort(key=lambda pair: (centers[pair[0]][1], centers[pair[1]][1]))
    for source, target in edges:
        edge = source, target
        chain = chains[edge]
        if edge in backward:
            sx, sy = positions[source]
            tx, ty = positions[target]
            route_y = margin / 2 + backward.index(edge) * 18
            points = [(sx + box_width, port(source, edge, True)),
                      (sx + box_width + 18, port(source, edge, True)),
                      (sx + box_width + 18, route_y), (tx - 18, route_y),
                      (tx - 18, port(target, edge, False)), (tx, port(target, edge, False))]
        else:
            points = []
            for segment, (left, right) in enumerate(zip(chain, chain[1:])):
                start_x, start_y = centers[left]
                end_x, end_y = centers[right]
                if segment == 0:
                    start_x += box_width / 2
                    start_y = port(source, edge, True)
                if segment == len(chain) - 2:
                    end_x -= box_width / 2
                    end_y = port(target, edge, False)
                group = gap_links[ranks[left]]
                gap_start = margin + ranks[left] * (box_width + column_gap) + box_width
                channel_x = gap_start + 15 + (column_gap - 30) * (group.index((left, right)) + 1) / (len(group) + 1)
                points.extend([(start_x, start_y), (channel_x, start_y),
                               (channel_x, end_y), (end_x, end_y)])
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
