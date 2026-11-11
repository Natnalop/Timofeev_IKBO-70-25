"""Только контрольное сравнение: приложение этот скрипт не импортирует."""
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
IMAGE = 'alpine@sha256:49340b346798875b5592e5d420241f2f9cfba5f47e62ebb1446a1b34734e898f'

def main():
    metadata = json.loads((HERE / 'snapshot.json').read_text())
    report = []
    for name, info in metadata['packages'].items():
        # Ровно тот же индекс; пустой root исключает влияние установленных пакетов.
        command = ['docker', 'run', '--rm', '-v', f'{HERE}:/data:ro', IMAGE, 'sh', '-ec',
            'mkdir -p /tmp/root/etc/apk /tmp/root/lib/apk/db /tmp/repo/x86_64; '
            'touch /tmp/root/lib/apk/db/installed; '
            'cp /data/APKINDEX.tar.gz /tmp/repo/x86_64/; '
            'apk --root /tmp/root --allow-untrusted --no-network '
            '--repositories-file /dev/null -X /tmp/repo dot "$1"', 'sh', name]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        (HERE / f'{name}.apk.dot').write_text(result.stdout, encoding='utf-8')
        (HERE / f'{name}.apk.stderr.txt').write_text(result.stderr, encoding='utf-8')
        if result.returncode:
            raise RuntimeError(result.stderr)
        native_edges = set(re.findall(r'"([^"\n]+)"\s*->\s*"([^"\n]+)"', result.stdout))
        d2_edges = set(re.findall(r'"([^"\n]+)"\s*->\s*"([^"\n]+)"', (HERE / f'{name}.d2').read_text()))
        normalize = lambda v: v.replace('@', '-')
        ours = {(normalize(a), normalize(b)) for a,b in d2_edges}
        entry = {'package':name, 'native_edges':len(native_edges), 'our_edges':len(ours),
                 'only_apk': sorted(native_edges - ours), 'only_ours': sorted(ours - native_edges),
                 'command': subprocess.list2cmdline(command)}
        report.append(entry)
    (HERE / 'comparison.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__': main()
