# Этап 4

Самостоятельный снимок приложения, Python 3.11+, внешние зависимости отсутствуют.

```powershell
cd Workbook2/stage4
python depgraph.py --config config.toml
python depgraph.py --config config.toml --reverse
```

Описание параметров и алгоритмов находится в [общем README](../README.md).
Примеры глубины, фильтра, цикла и изолированной вершины: `examples/*.toml`.
Фактический вывод демонстраций сохранен в `examples/demo.txt`.
