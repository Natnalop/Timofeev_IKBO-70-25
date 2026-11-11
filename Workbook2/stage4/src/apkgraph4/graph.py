"""Рекурсивный поиск в ширину и анализ обратных зависимостей."""


def bfs_recursive(root, neighbors, max_depth):
    """Обойти граф рекурсивно по слоям, сохраняя замыкающие цикл ребра."""
    nodes, edges, seen = {root}, set(), {root}

    def visit_level(frontier, depth):
        """Раскрыть текущий слой и рекурсивно обработать следующий."""
        if not frontier or depth >= max_depth:
            return
        next_level = []
        for current in frontier:
            for target in neighbors(current):
                nodes.add(target)
                edges.add((current, target))
                if target not in seen:
                    seen.add(target)
                    next_level.append(target)
        visit_level(next_level, depth + 1)

    visit_level([root], 0)
    return nodes, edges


def reverse_adjacency(repo, excluded):
    """Построить обратную смежность по всем пакетам репозитория."""
    incoming = {package: [] for package in repo.packages}
    for package in repo.packages:
        if excluded and excluded in package.name:
            continue
        for target in repo.dependencies(package, excluded):
            incoming[target].append(package)
    return incoming


def build_graph(repo, root, config, reverse=False):
    """Выбрать направление связей и выполнить рекурсивный BFS."""
    incoming = (
        reverse_adjacency(repo, config.filter_substring) if reverse else {}
    )

    def neighbors(package):
        """Получить соседние вершины с учетом выбранного направления."""
        if reverse:
            return sorted(incoming[package])
        return repo.dependencies(package, config.filter_substring)

    return bfs_recursive(root, neighbors, config.max_depth)
