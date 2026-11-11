"""Проверки конфигурации, APKINDEX и рекурсивного BFS."""

import gzip
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "depgraph", ROOT / "stage5/depgraph.py"
)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class GraphTests(unittest.TestCase):
    """Проверки рекурсивного BFS и операций над графом."""

    def setUp(self):
        """Подготовить независимые данные перед каждой проверкой."""
        self.a = m.Package("A", "1", ("B", "C"))
        self.b = m.Package("B", "1", ("D",))
        self.c = m.Package("C", "1", ("D",))
        self.d = m.Package("D", "1", ("A",))
        self.repo = m.Repository([self.a, self.b, self.c, self.d])

    def graph(self, depth=10, excluded="", reverse=False, root=None):
        """Построить тестовый граф с заданными ограничениями."""
        cfg = m.Config("A", "", True, "1", depth, excluded)
        return m.build_graph(self.repo, root or self.a, cfg, reverse)

    def test_cycle_and_diamond(self):
        """Проверить случай cycle and diamond."""
        nodes, edges = self.graph()
        self.assertEqual(len(nodes), 4)
        self.assertEqual(len(edges), 5)
        self.assertIn((self.d, self.a), edges)

    def test_depth_zero(self):
        """Проверить случай depth zero."""
        self.assertEqual(self.graph(0), ({self.a}, set()))

    def test_depth_one(self):
        """Проверить случай depth one."""
        self.assertEqual(self.graph(1)[0], {self.a, self.b, self.c})

    def test_shortest_path_is_bfs(self):
        """Проверить случай shortest path is bfs."""
        self.assertIn(self.d, self.graph(2)[0])
        self.assertNotIn((self.d, self.a), self.graph(2)[1])

    def test_filter(self):
        """Проверить случай filter."""
        nodes, edges = self.graph(excluded="B")
        self.assertNotIn(self.b, nodes)
        self.assertIn(self.d, nodes)

    def test_reverse(self):
        """Проверить случай reverse."""
        self.assertEqual(
            self.graph(1, reverse=True, root=self.d)[0],
            {self.b, self.c, self.d},
        )

    def test_reverse_cycle(self):
        """Проверить случай reverse cycle."""
        self.assertEqual(len(self.graph(reverse=True)[0]), 4)

    def test_isolated(self):
        """Проверить случай isolated."""
        p = m.Package("Z", "1")
        self.assertEqual(m.bfs_recursive(p, lambda _: [], 200), ({p}, set()))

    def test_d2_deterministic(self):
        """Проверить случай d2 deterministic."""
        nodes, edges = self.graph()
        text = m.to_d2(nodes, edges)
        self.assertEqual(text.count(" -> "), 5)
        self.assertEqual(text, m.to_d2(set(reversed(sorted(nodes))), edges))


class RepositoryTests(unittest.TestCase):
    """Проверки индекса, версий и виртуальных зависимостей."""

    def test_index_virtual_and_conflict(self):
        """Проверить случай index virtual and conflict."""
        repo = m.parse_index(
            "P:app\nV:2-r0\nD:so:libc.so=1 !bad\n\n"
            "P:musl\nV:1.2-r0\np:so:libc.so=1\n"
        )
        self.assertEqual(
            repo.dependencies(repo.root("app", "2-r0"))[0].name, "musl"
        )

    def test_exact_version(self):
        """Проверить случай exact version."""
        repo = m.Repository([m.Package("A", "1"), m.Package("A", "2")])
        self.assertEqual(repo.root("A", "1").version, "1")
        with self.assertRaises(m.AppError):
            repo.root("A", "3")

    def test_missing(self):
        """Проверить случай missing."""
        with self.assertRaises(m.AppError):
            m.Repository([]).resolve("absent")

    def test_duplicate(self):
        """Проверить случай duplicate."""
        with self.assertRaises(m.AppError):
            m.Repository([m.Package("A", "1")] * 2)

    def test_bad_index(self):
        """Проверить случай bad index."""
        for value in ("P:A", "broken", ""):
            with self.subTest(value=value), self.assertRaises(m.AppError):
                m.parse_index(value)

    def test_constraints(self):
        """Проверить случай constraints."""
        for op, version, wanted, expected in [
            (">", "1.10", "1.9", True),
            ("<", "1_rc1", "1", True),
            (">", "1_p1", "1", True),
            (">=", "1-r10", "1-r2", True),
            ("=", "1", "2", False),
            ("~", "1.2.3-r0", "1.2", True),
            ("~", "1.20", "1.2", False),
        ]:
            with self.subTest(op=op, version=version):
                self.assertEqual(
                    bool(m.satisfies(version, op, wanted)), expected
                )

    def test_download_archive(self):
        """Проверить случай download archive."""
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode="w:gz") as archive:
            text = b"P:app\nV:1\n"
            info = tarfile.TarInfo("APKINDEX")
            info.size = len(text)
            archive.addfile(info, io.BytesIO(text))
        cfg = m.Config("app", "https://example.org/x86_64", False, "1", 2, "")
        with patch.object(
            m, "urlopen", return_value=io.BytesIO(output.getvalue())
        ) as request:
            self.assertEqual(
                m.load_repository(cfg).root("app", "1").name, "app"
            )
            self.assertEqual(
                request.call_args.args[0],
                "https://example.org/x86_64/APKINDEX.tar.gz",
            )

    def test_bad_archive_and_network(self):
        """Проверить случай bad archive and network."""
        cfg = m.Config("app", "https://example.org", False, "1", 2, "")
        with (
            patch.object(m, "urlopen", side_effect=OSError("offline")),
            self.assertRaises(m.AppError),
        ):
            m.load_repository(cfg)

    def test_signed_concatenated_gzip(self):
        """Проверить случай signed concatenated gzip."""

        def member(name, text):
            """Создать gzip-поток с одним членом тестового tar-архива."""
            output = io.BytesIO()
            with tarfile.open(fileobj=output, mode="w:") as archive:
                info = tarfile.TarInfo(name)
                info.size = len(text)
                archive.addfile(info, io.BytesIO(text))
            return gzip.compress(output.getvalue())

        blob = member(".SIGN.RSA.test", b"signature") + member(
            "APKINDEX", b"P:app\nV:1\n"
        )
        cfg = m.Config("app", "https://example.org", False, "1", 2, "")
        with patch.object(m, "urlopen", return_value=io.BytesIO(blob)):
            self.assertEqual(
                m.load_repository(cfg).root("app", "1").name, "app"
            )
        with (
            patch.object(m, "urlopen", return_value=io.BytesIO(b"bad")),
            self.assertRaises(m.AppError),
        ):
            m.load_repository(cfg)


class ConfigTests(unittest.TestCase):
    """Проверки типов, путей и ошибок конфигурации."""

    def setUp(self):
        """Подготовить независимые данные перед каждой проверкой."""
        (ROOT / "tmp").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "tmp")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "config.toml"
        (self.path.parent / "repo.json").write_text(
            '{"A":{"version":"1","dependencies":[]}}'
        )
        self.valid = dict(
            package="A",
            repository="repo.json",
            test_mode=True,
            version="1",
            max_depth=5,
            filter_substring="",
        )

    def write(self, data):
        """Записать временную TOML-конфигурацию для проверки."""
        self.path.write_text(
            "\n".join(f"{k} = {json.dumps(v)}" for k, v in data.items()),
            encoding="utf-8",
        )

    def test_relative_path(self):
        """Проверить случай relative path."""
        self.write(self.valid)
        self.assertEqual(
            m.load_config(self.path).repository,
            str(self.path.parent / "repo.json"),
        )

    def test_each_parameter(self):
        """Проверить случай each parameter."""
        invalid = dict(
            package="a",
            repository="absent",
            test_mode="yes",
            version="",
            max_depth=-1,
            filter_substring=12,
        )
        for key, value in invalid.items():
            with self.subTest(parameter=key):
                self.write(self.valid | {key: value})
                with self.assertRaises(m.AppError):
                    m.load_config(self.path)

    def test_extra_and_missing_and_bool_depth(self):
        """Проверить случай extra and missing and bool depth."""
        for value in (
            self.valid | {"other": 1},
            self.valid | {"max_depth": True},
            {"package": "A"},
            self.valid | {"filter_substring": "A"},
        ):
            self.write(value)
            with self.assertRaises(m.AppError):
                m.load_config(self.path)

    def test_bad_url(self):
        """Проверить случай bad url."""
        self.write(
            self.valid | {"test_mode": False, "repository": "file:///tmp/repo"}
        )
        with self.assertRaises(m.AppError):
            m.load_config(self.path)

    def test_missing_and_broken_toml(self):
        """Проверить случай missing and broken toml."""
        with self.assertRaises(m.AppError):
            m.load_config(self.path)
        self.path.write_text("broken = [")
        with self.assertRaises(m.AppError):
            m.load_config(self.path)

    def test_json_missing_dependency(self):
        """Проверить случай json missing dependency."""
        self.write(self.valid)
        (self.path.parent / "repo.json").write_text(
            '{"A":{"version":"1","dependencies":["B"]}}'
        )
        with self.assertRaises(m.AppError):
            m.load_repository(m.load_config(self.path))

    def test_cli_stages(self):
        """Проверить случай cli stages."""
        self.write(self.valid)
        for stage in range(1, 6):
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / f"stage{stage}/depgraph.py"),
                    "--config",
                    str(self.path),
                ],
                capture_output=True,
                env=os.environ | {"PYTHONIOENCODING": "utf-8"},
            )
            with self.subTest(stage=stage):
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
