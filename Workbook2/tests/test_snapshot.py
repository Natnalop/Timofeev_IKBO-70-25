"""Регрессионные проверки текстового снимка и контрольных графов Alpine."""

import hashlib
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "stage5/examples"
sys.path.insert(0, str(ROOT / "stage5"))
sys.path.insert(0, str(EXAMPLES))

import compare_apk  # noqa: E402
import depgraph as graph  # noqa: E402


class SnapshotTests(unittest.TestCase):
    """Проверки неизменности данных и переносов строк для apk-tools."""

    def test_subset_checksum(self):
        """Текстовый снимок соответствует сохраненной контрольной сумме."""
        metadata = json.loads((EXAMPLES / "snapshot.json").read_text())
        data = (EXAMPLES / "APKINDEX.txt").read_text("utf-8").encode()
        self.assertEqual(
            hashlib.sha256(data).hexdigest(), metadata["subset_sha256"]
        )

    def test_archive_has_unix_newlines(self):
        """Временный индекс совместим с apk при Windows-переносах в Git."""
        temporary = ROOT / "tmp"
        temporary.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary) as folder:
            compare_apk.make_archive(Path(folder))
            with tarfile.open(Path(folder) / "APKINDEX.tar.gz") as archive:
                data = archive.extractfile("APKINDEX").read()
        self.assertNotIn(b"\r", data)
        repo = graph.parse_index(data.decode())
        self.assertIn("curl", repo.names)

    def test_saved_native_edges_match(self):
        """Все три сохраненных штатных графа совпадают с D2 по ребрам."""
        for name in ("busybox", "zlib", "curl"):
            with self.subTest(package=name):
                result = compare_apk.compare_edges(name, "saved")
                self.assertEqual(result["only_apk"], [])
                self.assertEqual(result["only_ours"], [])
