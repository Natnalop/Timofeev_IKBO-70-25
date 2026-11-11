"""Воспроизводимые примеры из сохраненного официального APKINDEX."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import depgraph as d
from svg_renderer import to_svg

def main():
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
        (HERE / f'{name}.svg').write_text(to_svg(nodes, edges), encoding='utf-8')
        (HERE / f'{name}.toml').write_text('\n'.join(f'{k} = {json.dumps(v)}' for k,v in vars(config).items())+'\n', encoding='utf-8')
        metadata['packages'][name] = {'version': package.version, 'nodes': len(nodes), 'edges': len(edges)}
    (HERE / 'snapshot.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')

if __name__ == '__main__': main()
