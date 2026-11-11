"""Собрать самостоятельные снимки этапов из финальной реализации."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    source = (ROOT / 'stage5' / 'depgraph.py').read_text(encoding='utf-8')
    for stage in range(1, 5):
        folder = ROOT / f'stage{stage}'
        folder.mkdir(exist_ok=True)
        (folder / 'depgraph.py').write_text(source.replace('STAGE = 5', f'STAGE = {stage}'), encoding='utf-8')

if __name__ == '__main__':
    main()
