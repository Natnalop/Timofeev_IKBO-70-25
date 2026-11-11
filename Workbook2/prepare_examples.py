"""Создать автономные конфигурации и демонстрационные протоколы всех этапов."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def config(package='A', repository='repository.json', test=True, version='1.0', depth=10, excluded=''):
    values = dict(package=package, repository=repository, test_mode=test, version=version,
                  max_depth=depth, filter_substring=excluded)
    return '\n'.join(f'{k} = {json.dumps(v, ensure_ascii=False)}' for k,v in values.items()) + '\n'

def main():
    graph = {'A': ['B', 'C'], 'B': ['D'], 'C': ['D', 'E'], 'D': ['A'], 'E': [], 'Z': []}
    for stage in range(1, 6):
        folder = ROOT / f'stage{stage}'
        folder.mkdir(exist_ok=True)
        (folder / 'repository.json').write_text(json.dumps({n: dict(version='1.0', dependencies=d) for n,d in graph.items()}, indent=2), encoding='utf-8')
        (folder / 'config.toml').write_text(config(), encoding='utf-8')
        examples = folder / 'examples'; examples.mkdir(exist_ok=True)
        for name, kwargs in {'cycle': {}, 'depth1': {'depth': 1}, 'depth0': {'depth': 0}, 'filter': {'excluded': 'B'}, 'isolated': {'package': 'Z'}}.items():
            (examples / f'{name}.toml').write_text(config(repository='../repository.json', **kwargs), encoding='utf-8')
        transcript = []
        cases = ['cycle', 'depth1', 'depth0', 'filter', 'isolated'] if stage >= 3 else ['cycle']
        for name in cases:
            commands = [False, True] if stage == 4 else [False]
            for reverse in commands:
                args = [sys.executable, str(folder / 'depgraph.py'), '--config', str(examples / f'{name}.toml')]
                if reverse: args.append('--reverse')
                result = subprocess.run(args, capture_output=True, encoding='utf-8', env=__import__('os').environ | {'PYTHONIOENCODING':'utf-8'})
                transcript.append(f'CASE {name}, reverse={reverse}, exit={result.returncode}\n{result.stdout}{result.stderr}')
        (examples / 'demo.txt').write_text('\n'.join(transcript), encoding='utf-8')
        (folder / 'README.md').write_text(f'''# Этап {stage}

Самостоятельный снимок приложения, Python 3.11+, внешние зависимости отсутствуют.

```powershell
cd Workbook2/stage{stage}
python depgraph.py --config config.toml
'''+('python depgraph.py --config config.toml --reverse\n' if stage == 4 else '')+'''```

Описание параметров и алгоритмов находится в [общем README](../README.md).
Примеры глубины, фильтра, цикла и изолированной вершины: `examples/*.toml`.
Фактический вывод демонстраций сохранен в `examples/demo.txt`.
''', encoding='utf-8')
    # Ошибки каждого из шести параметров на этапе 1.
    cases = dict(package={'package':'bad name'}, repository={'repository':'missing.json'},
                 test_mode={'test':'yes'}, version={'version':''}, max_depth={'depth':-1}, filter_substring={'excluded':'A'})
    transcript = []
    for name, kwargs in cases.items():
        path = ROOT / 'stage1/examples' / f'invalid_{name}.toml'
        path.write_text(config(repository='../repository.json', **kwargs) if name != 'repository' else config(**kwargs), encoding='utf-8')
        result = subprocess.run([sys.executable, str(ROOT / 'stage1/depgraph.py'), '--config', str(path)], capture_output=True, encoding='utf-8', env=__import__('os').environ | {'PYTHONIOENCODING':'utf-8'})
        transcript.append(f'{name}: exit={result.returncode}\n{result.stderr}')
    (ROOT / 'stage1/examples/errors.txt').write_text('\n'.join(transcript), encoding='utf-8')

if __name__ == '__main__': main()
