"""Граф зависимостей Alpine APK. Только стандартная библиотека Python 3.11+."""
from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import sys
import tarfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

STAGE = 5
MAX_BYTES = 32 * 1024 * 1024

class AppError(ValueError):
    """Ожидаемая ошибка входных данных."""

@dataclass(frozen=True)
class Config:
    package: str
    repository: str
    test_mode: bool
    version: str
    max_depth: int
    filter_substring: str

def load_config(path: Path) -> Config:
    try:
        with path.open('rb') as stream:
            data = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise AppError(f'TOML: {exc}') from exc
    types = dict(package=str, repository=str, test_mode=bool, version=str,
                 max_depth=int, filter_substring=str)
    errors = []
    for key, kind in types.items():
        if key not in data or type(data[key]) is not kind:
            errors.append(f'{key}: требуется {kind.__name__}')
    errors.extend(f'{key}: неизвестный параметр' for key in data.keys() - types.keys())
    if errors:
        raise AppError('; '.join(errors))
    name_pattern = r'[A-Z]+' if data['test_mode'] else r'[a-zA-Z0-9][a-zA-Z0-9+_.-]*'
    if not re.fullmatch(name_pattern, data['package']):
        errors.append('package: недопустимое имя пакета')
    if not re.fullmatch(r'[0-9][a-zA-Z0-9._+-]*', data['version']):
        errors.append('version: требуется непустая версия, начинающаяся с цифры')
    if not 0 <= data['max_depth'] <= 200:
        errors.append('max_depth: допустимо целое число от 0 до 200')
    if any(ord(c) < 32 for c in data['filter_substring']):
        errors.append('filter_substring: управляющие символы запрещены')
    if data['filter_substring'] and data['filter_substring'] in data['package']:
        errors.append('filter_substring: фильтр исключает корневой пакет')
    if data['test_mode']:
        local = Path(data['repository'])
        if not local.is_absolute():
            local = path.resolve().parent / local
        if not local.is_file():
            errors.append('repository: файл тестового репозитория не найден')
        data['repository'] = str(local)
    else:
        try:
            parsed = urlparse(data['repository'])
            valid_url = parsed.scheme in ('http', 'https') and parsed.hostname and not parsed.query and not parsed.fragment
            _ = parsed.port
        except ValueError:
            valid_url = False
        if not valid_url:
            errors.append('repository: требуется HTTP(S) URL каталога архитектуры или APKINDEX.tar.gz')
    if errors:
        raise AppError('; '.join(errors))
    return Config(**data)

@dataclass(frozen=True, order=True)
class Package:
    name: str
    version: str
    dependencies: tuple[str, ...] = ()
    provides: tuple[str, ...] = ()

    @property
    def key(self):
        return f'{self.name}@{self.version}'

DEP = re.compile(r'([^<>=~\s]+)(<=|>=|=|<|>|~)?([^\s]*)')

def split_dependency(value):
    match = DEP.fullmatch(value)
    if not match or (match[2] and not match[3]) or (not match[2] and match[3]):
        raise AppError(f'Некорректная зависимость: {value}')
    return match[1], match[2] or '', match[3]

def version_key(version):
    """Числовые части и суффиксы Alpine; не лексикографическая сортировка."""
    main, _, revision = version.partition('-r')
    parts = main.split('_')
    base = tuple((1, int(t)) if t.isdigit() else (0, t)
                 for t in re.findall(r'\d+|[a-zA-Z]+', parts[0]))
    ranks = dict(alpha=-4, beta=-3, pre=-2, rc=-1, cvs=1, svn=2, git=3, hg=4, p=5)
    suffixes = []
    for suffix in parts[1:]:
        match = re.fullmatch(r'([a-z]+)(\d*)', suffix)
        if not match or match[1] not in ranks:
            raise AppError(f'Неподдерживаемая версия: {version}')
        suffixes.append((ranks[match[1]], int(match[2] or 0)))
    return base, tuple(suffixes or [(0, 0)]), int(revision or 0)

def satisfies(actual, op, wanted):
    if not op:
        return True
    if op == '=':
        return actual == wanted
    if op == '~':
        return actual == wanted or actual.startswith(wanted + '.') or actual.startswith(wanted + '-r')
    a, b = version_key(actual), version_key(wanted)
    return {'<': a < b, '>': a > b, '<=': a <= b, '>=': a >= b}[op]

class Repository:
    def __init__(self, packages):
        self.packages = sorted(packages)
        self.names = {}
        self.providers = {}
        for package in self.packages:
            if any(p.version == package.version for p in self.names.get(package.name, [])):
                raise AppError(f'Повтор пакета: {package.key}')
            self.names.setdefault(package.name, []).append(package)
            for provide in package.provides:
                name, op, version = split_dependency(provide)
                self.providers.setdefault(name, []).append((package, version if op else ''))

    def root(self, name, version):
        for package in self.names.get(name, []):
            if package.version == version:
                return package
        raise AppError(f'Пакет {name} версии {version} не найден')

    def resolve(self, dependency):
        name, op, wanted = split_dependency(dependency)
        candidates = [p for p in self.names.get(name, []) if satisfies(p.version, op, wanted)]
        if not candidates:
            candidates = [p for p, v in self.providers.get(name, [])
                          if not op or (v and satisfies(v, op, wanted))]
        if not candidates:
            raise AppError(f'Зависимость {dependency} отсутствует в выбранном репозитории')
        # Визуализатор выбирает одну ветвь, а не решает задачу установки пакетов.
        return sorted(candidates, key=lambda p: (version_key(p.version), p.name))[-1]

    def dependencies(self, package, excluded=''):
        result = []
        for dep in package.dependencies:
            if dep.startswith('!'):  # конфликт не является ребром зависимости
                continue
            name, _, _ = split_dependency(dep)
            if excluded and excluded in name:
                continue
            target = self.resolve(dep)
            if not excluded or excluded not in target.name:
                result.append(target)
        return sorted(set(result))

def parse_index(text):
    packages = []
    for record in re.split(r'\n\s*\n', text.strip()):
        fields = {}
        for line in record.splitlines():
            if len(line) < 2 or line[1] != ':':
                raise AppError('Поврежден APKINDEX: ожидается поле X:значение')
            fields[line[0]] = line[2:]
        if not fields.get('P') or not fields.get('V'):
            raise AppError('APKINDEX: отсутствует P или V')
        packages.append(Package(fields['P'], fields['V'], tuple(fields.get('D', '').split()),
                                tuple(fields.get('p', '').split())))
    return Repository(packages)

def load_repository(config):
    if config.test_mode:
        try:
            data = json.loads(Path(config.repository).read_text(encoding='utf-8'))
            if type(data) is not dict or not data:
                raise AppError('JSON: требуется непустой объект пакетов')
            packages = []
            for name, record in data.items():
                if not re.fullmatch('[A-Z]+', name) or type(record) is not dict:
                    raise AppError('JSON: имена пакетов должны состоять из A-Z')
                if set(record) != {'version', 'dependencies'} or type(record['version']) is not str or not re.fullmatch(r'[0-9][a-zA-Z0-9._+-]*', record['version']):
                    raise AppError(f'JSON: неверная запись {name}')
                deps = record['dependencies']
                if type(deps) is not list or any(type(d) is not str or not re.fullmatch('[A-Z]+', d) for d in deps):
                    raise AppError(f'JSON: неверные зависимости {name}')
                packages.append(Package(name, record['version'], tuple(deps)))
            repo = Repository(packages)
            for package in packages:
                repo.dependencies(package)
            return repo
        except (OSError, json.JSONDecodeError) as exc:
            raise AppError(f'JSON: {exc}') from exc
    url = config.repository.rstrip('/')
    if not url.endswith('APKINDEX.tar.gz'):
        url += '/APKINDEX.tar.gz'
    try:
        with urlopen(url, timeout=30) as response:
            blob = response.read(MAX_BYTES + 1)
        if len(blob) > MAX_BYTES:
            raise AppError('Архив APKINDEX превышает 32 МиБ')
        # Подписанные индексы APK содержат несколько склеенных gzip-потоков.
        # gzip.GzipFile читает все потоки; tarfile r|gz останавливается на первом.
        with gzip.GzipFile(fileobj=io.BytesIO(blob)) as zipped:
            unpacked = zipped.read(MAX_BYTES + 1)
        if len(unpacked) > MAX_BYTES:
            raise AppError('Распакованный архив APKINDEX превышает 32 МиБ')
        with tarfile.open(fileobj=io.BytesIO(unpacked), mode='r:', ignore_zeros=True) as archive:
            for member in archive:
                if member.name == 'APKINDEX' and member.isfile():
                    if member.size > MAX_BYTES:
                        raise AppError('APKINDEX превышает 32 МиБ')
                    return parse_index(archive.extractfile(member).read().decode('utf-8'))
        raise AppError('В архиве отсутствует APKINDEX')
    except (OSError, tarfile.TarError, UnicodeError, EOFError) as exc:
        raise AppError(f'Ошибка чтения APKINDEX: {exc}') from exc

def bfs_recursive(root, neighbors, max_depth):
    """Рекурсия по слоям очереди BFS, а не обход DFS по отдельным вершинам."""
    nodes, edges, seen = {root}, set(), {root}
    def visit_level(frontier, depth):
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

def build_graph(repo, root, config, reverse=False):
    if reverse:
        incoming = {p: [] for p in repo.packages}
        for package in repo.packages:
            if config.filter_substring and config.filter_substring in package.name:
                continue
            for target in repo.dependencies(package, config.filter_substring):
                incoming[target].append(package)
        neighbors = lambda p: sorted(incoming[p])
    else:
        neighbors = lambda p: repo.dependencies(p, config.filter_substring)
    return bfs_recursive(root, neighbors, config.max_depth)

def to_d2(nodes, edges):
    quote = lambda text: json.dumps(text, ensure_ascii=False)
    lines = ['direction: right', 'vars: {', '  d2-config: {', '    layout-engine: elk', '  }', '}', 'style.fill: white']
    for p in sorted(nodes):
        lines.extend([f'{quote(p.key)}: {quote(p.name + chr(10) + p.version)} {{',
                      '  shape: rectangle', '  style.fill: white', '  style.stroke: black',
                      '  style.font-color: black', '  style.stroke-width: 1',
                      '  style.border-radius: 0', '  style.shadow: false', '  style.font-size: 18', '}'])
    for a, b in sorted(edges):
        lines.extend([f'{quote(a.key)} -> {quote(b.key)} {{', '  style.stroke: black',
                      '  style.stroke-width: 1', '  style.border-radius: 0', '}'])
    return '\n'.join(lines) + '\n'

def main(argv=None):
    parser = argparse.ArgumentParser(description=f'APK dependency graph, этап {STAGE}')
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('config.toml'))
    if STAGE == 4:
        parser.add_argument('--reverse', action='store_true', help='обратные транзитивные зависимости')
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if STAGE == 1:
            for key, value in vars(config).items():
                print(f'{key} = {json.dumps(value, ensure_ascii=False)}')
            return 0
        repo = load_repository(config)
        root = repo.root(config.package, config.version)
        if STAGE == 2:
            for dependency in root.dependencies:
                if not dependency.startswith('!'):
                    print(dependency)
            return 0
        nodes, edges = build_graph(repo, root, config, getattr(args, 'reverse', False))
        if STAGE == 5:
            print(to_d2(nodes, edges), end='')
        else:
            print('Узлы: ' + ', '.join(p.key for p in sorted(nodes)))
            for a, b in sorted(edges):
                print(f'{a.key} -> {b.key}')
        return 0
    except (AppError, RecursionError) as exc:
        print(f'Ошибка: {exc}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
