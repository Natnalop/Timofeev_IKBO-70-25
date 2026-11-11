"""Контрольное сравнение D2 с apk dot; приложение этот файл не вызывает."""

import argparse
import io
import json
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGE = (
    "alpine@sha256:"
    "49340b346798875b5592e5d420241f2f9cfba5f47e62ebb1446a1b34734e898f"
)
EDGE_PATTERN = r'"([^"\n]+)"\s*->\s*"([^"\n]+)"'
CONTAINER_SCRIPT = (
    "mkdir -p /tmp/root/etc/apk /tmp/root/lib/apk/db /tmp/repo/x86_64; "
    "touch /tmp/root/lib/apk/db/installed; "
    "cp /data/APKINDEX.tar.gz /tmp/repo/x86_64/; "
    "apk --root /tmp/root --allow-untrusted --no-network "
    '--repositories-file /dev/null -X /tmp/repo dot "$1"'
)


def make_archive(folder):
    """Создать временный индекс для apk dot, не храня архив в Git."""
    data = (HERE / "APKINDEX.txt").read_text("utf-8").encode("utf-8")
    with tarfile.open(folder / "APKINDEX.tar.gz", "w:gz") as archive:
        member = tarfile.TarInfo("APKINDEX")
        member.size = len(data)
        archive.addfile(member, io.BytesIO(data))


def collect_native(name, folder):
    """Запустить штатный apk dot в контейнере с пустой базой пакетов."""
    command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{folder}:/data:ro",
        IMAGE,
        "sh",
        "-ec",
        CONTAINER_SCRIPT,
        "sh",
        name,
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode:
        details = result.stderr or result.stdout
        raise RuntimeError(
            f"Docker exit={result.returncode}: {details}\n"
            + subprocess.list2cmdline(command)
        )
    (HERE / f"{name}.apk.dot").write_text(result.stdout, encoding="utf-8")
    (HERE / f"{name}.apk.stderr.txt").write_text(
        result.stderr, encoding="utf-8"
    )
    return command


def compare_edges(name, command):
    """Сравнить множества ребер с нормализацией разделителя версии."""
    native = (HERE / f"{name}.apk.dot").read_text("utf-8")
    diagram = (HERE / f"{name}.d2").read_text("utf-8")
    native_edges = set(re.findall(EDGE_PATTERN, native))
    ours = {
        (left.replace("@", "-"), right.replace("@", "-"))
        for left, right in re.findall(EDGE_PATTERN, diagram)
    }
    return {
        "package": name,
        "native_edges": len(native_edges),
        "our_edges": len(ours),
        "only_apk": sorted(native_edges - ours),
        "only_ours": sorted(ours - native_edges),
        "command": command,
    }


def main():
    """Сравнить новые результаты Docker или сохраненные протоколы apk."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saved", action="store_true")
    args = parser.parse_args()
    metadata = json.loads((HERE / "snapshot.json").read_text("utf-8"))
    temporary = HERE.parents[1] / "tmp"
    temporary.mkdir(exist_ok=True)
    report = []
    with tempfile.TemporaryDirectory(dir=temporary) as name:
        folder = Path(name)
        make_archive(folder)
        for package in metadata["packages"]:
            command = "saved apk dot output"
            if not args.saved:
                command = collect_native(package, folder)
            report.append(compare_edges(package, command))
    text = json.dumps(report, indent=2)
    (HERE / "comparison.json").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
