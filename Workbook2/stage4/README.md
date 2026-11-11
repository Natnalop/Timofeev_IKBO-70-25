# Этап 4

Самостоятельный снимок приложения, Python 3.11+, внешние зависимости отсутствуют.

## Запуск

```powershell
cd Workbook2/stage4
python depgraph.py --config config.toml
python depgraph.py --config config.toml --reverse
```

Описание параметров и алгоритмов находится в [общем README](../README.md). Примеры глубины, фильтра,
цикла и изолированной вершины: `examples/*.toml`. Фактический вывод демонстраций сохранен в
`examples/demo.txt`.

## Исходники и проверки

Реализация находится в `src/apkgraph4`: `config.py` проверяет TOML, `index.py` читает APKINDEX,
`repository.py` разрешает зависимости, `graph.py` содержит рекурсивный BFS и обратную смежность.
Прежний `depgraph.py` теперь является короткой точкой входа.

```powershell
.\run.bat --reverse
python -m unittest discover -s tests -v
```
