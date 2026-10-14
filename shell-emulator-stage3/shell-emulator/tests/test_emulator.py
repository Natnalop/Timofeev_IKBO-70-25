"""Модульные тесты ядра эмулятора и VFS.

Запуск из корня репозитория: ``PYTHONPATH=src python3 -m unittest
discover -s tests``.
"""
import os
import tempfile
import unittest
import zipfile
from unittest import mock

from shell import Shell, expand_env
from vfs import VFS, VFSError

MIN_DEPTH_PATH = "a/b/c/d.txt"


def make_zip(directory, name, files):
    """Создаёт во временной папке архив и возвращает путь к нему."""
    path = os.path.join(directory, name)
    with zipfile.ZipFile(path, "w") as archive:
        for entry, content in files.items():
            archive.writestr(entry, content)
    return path


def find(vfs, path):
    """Находит узел VFS по пути или возвращает None."""
    node = vfs.root
    for part in path.split("/"):
        node = node.children.get(part) if node.children else None
        if node is None:
            return None
    return node


class ShellTest(unittest.TestCase):
    """Тесты парсера и команд."""

    def setUp(self):
        """Создаёт оболочку с VFS по умолчанию."""
        self.shell = Shell(VFS.default(), "> ")

    def test_stub_prints_name_and_args(self):
        """Заглушки печатают своё имя и аргументы."""
        self.assertEqual(self.shell.run("ls -l /tmp").out, "ls -l /tmp")
        self.assertEqual(self.shell.run("cd /home").out, "cd /home")

    def test_unknown_command(self):
        """Неизвестная команда даёт ошибку."""
        result = self.shell.run("foo bar")
        self.assertFalse(result.ok)
        self.assertIn("команда не найдена", result.out)

    def test_cd_too_many_args(self):
        """cd с двумя аргументами - ошибка."""
        self.assertFalse(self.shell.run("cd a b").ok)

    def test_exit(self):
        """exit завершает работу, а с аргументами - ошибка."""
        self.assertTrue(self.shell.run("exit").should_exit)
        self.assertFalse(self.shell.run("exit now").ok)

    def test_env_expansion(self):
        """Переменные окружения раскрываются."""
        with mock.patch.dict(os.environ, {"HOME": "/home/tester"}):
            self.assertEqual(expand_env("ls $HOME"), "ls /home/tester")
            result = self.shell.run("ls ${HOME}/x")
        self.assertEqual(result.out, "ls /home/tester/x")

    def test_unclosed_quote(self):
        """Незакрытая кавычка - ошибка разбора."""
        self.assertFalse(self.shell.run('ls "abc').ok)

    def test_script_skips_bad_lines(self):
        """Скрипт пропускает ошибки и останавливается на exit."""
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "script.txt")
            with open(path, "w", encoding="utf-8") as file:
                file.write("foo\nls ok\nexit\nls after\n")
            lines = []
            stopped = self.shell.run_script(path, lines.append)
        self.assertTrue(stopped)
        self.assertIn("foo: команда не найдена", lines)
        self.assertIn("ls ok", lines)
        self.assertNotIn("> ls after", lines)

    def test_script_not_found(self):
        """Отсутствующий скрипт сообщает об ошибке."""
        lines = []
        self.shell.run_script("no_such_script.txt", lines.append)
        self.assertIn("[скрипт] ошибка", lines[0])


class VFSTest(unittest.TestCase):
    """Тесты виртуальной файловой системы."""

    def setUp(self):
        """Создаёт временную папку для архивов."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.directory = tmp.name

    def test_default_has_readme(self):
        """VFS по умолчанию содержит readme.txt."""
        node = find(VFS.default(), "home/user/readme.txt")
        self.assertFalse(node.is_dir)
        self.assertFalse(node.is_binary())

    def test_binary_is_base64(self):
        """Двоичный файл выводится в формате base64."""
        node = find(VFS.default(), "home/user/pixel.png")
        self.assertTrue(node.is_binary())
        self.assertTrue(node.as_text().startswith("base64:"))

    def test_from_zip_nested(self):
        """Вложенные папки из архива загружаются в память."""
        path = make_zip(self.directory, "t.zip", {MIN_DEPTH_PATH: "x"})
        vfs = VFS.from_zip(path)
        self.assertEqual(find(vfs, MIN_DEPTH_PATH).data, b"x")

    def test_missing_file(self):
        """Отсутствующий архив - VFSError."""
        with self.assertRaises(VFSError):
            VFS.from_zip(os.path.join(self.directory, "none.zip"))

    def test_bad_format(self):
        """Файл, не являющийся ZIP, - VFSError."""
        path = os.path.join(self.directory, "bad.zip")
        with open(path, "w", encoding="utf-8") as file:
            file.write("not a zip")
        with self.assertRaises(VFSError):
            VFS.from_zip(path)

    def test_unsafe_path(self):
        """Путь с .. внутри архива отклоняется."""
        path = make_zip(self.directory, "u.zip", {"../evil.txt": "x"})
        with self.assertRaises(VFSError):
            VFS.from_zip(path)


if __name__ == "__main__":
    unittest.main()
