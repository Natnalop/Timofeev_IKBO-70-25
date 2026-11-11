"""Воспроизводимые примеры из сохраненного официального APKINDEX."""
import hashlib
import argparse
import json
from pathlib import Path
import sys
import tarfile
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import depgraph as d
from svg_renderer import to_svg

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer', choices=('d2', 'python'), default='d2',
                        help='d2: прежнее оформление; python: собственная отрисовка SVG')
    args = parser.parse_args()
    local_d2 = HERE.parents[1] / '.tools' / 'd2.exe'
    d2_command = str(local_d2) if local_d2.is_file() else shutil.which('d2')
    if args.renderer == 'd2' and not d2_command:
        parser.error('Для прежнего оформления нужен D2 в PATH или Workbook2/.tools/d2.exe. '
                     'Для отрисовки без D2 используйте --renderer python.')
    archive_path = HERE / 'APKINDEX.tar.gz'
    with tarfile.open(archive_path) as archive:
        repo = d.parse_index(archive.extractfile('APKINDEX').read().decode('utf-8'))
    metadata = {'url': 'https://dl-cdn.alpinelinux.org/alpine/v3.22/main/x86_64/APKINDEX.tar.gz',
                'date': '2026-11-11', 'sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(), 'packages': {}}
    for name in ('busybox', 'zlib', 'curl'):
        package = repo.names[name][-1]
        config = d.Config(name, metadata['url'], False, package.version, 20, '')
        nodes, edges = d.build_graph(repo, package, config)
        (HERE / f'{name}.d2').write_text(d.to_d2(nodes, edges), encoding='utf-8')
        if args.renderer == 'python':
            (HERE / f'{name}.svg').write_text(to_svg(nodes, edges), encoding='utf-8')
        else:
            subprocess.run([d2_command, str(HERE / f'{name}.d2'), str(HERE / f'{name}.svg')], check=True)
        (HERE / f'{name}.toml').write_text('\n'.join(f'{k} = {json.dumps(v)}' for k,v in vars(config).items())+'\n', encoding='utf-8')
        metadata['packages'][name] = {'version': package.version, 'nodes': len(nodes), 'edges': len(edges)}
    (HERE / 'snapshot.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')

if __name__ == '__main__': main()
