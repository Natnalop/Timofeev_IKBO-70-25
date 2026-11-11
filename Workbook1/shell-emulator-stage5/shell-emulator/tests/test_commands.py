"""Модульные тесты команд этапа 4: ls, cd, history, who, head."""
import os
import tempfile
import unittest

from helpers import make_zip
from shell import Shell
from vfs import VFS

LONG_COUNT = 15
LONG_TEXT = "".join(f"{n}\n" for n in range(1, LONG_COUNT + 1))
HOME = ["home", "user"]
DOCS = ["home", "user", "docs"]


def build_shell(prompt="> "):
    """Создаёт оболочку с небольшой VFS для проверки команд."""
    vfs = VFS()
    vfs.add_file("home/user/docs/long.txt", LONG_TEXT.encode("utf-8"))
    vfs.add_file("home/user/docs/a.txt", b"one\ntwo\n")
    vfs.add_file("home/user/.hidden", b"")
    vfs.add_file("home/user/bin.dat", bytes([0, 255, 254]))
    vfs.add_dir("tmp")
    return Shell(vfs, prompt)


class LsTest(unittest.TestCase):
    """Тесты команды ls."""

    def setUp(self):
        """Создаёт оболочку."""
        self.shell = build_shell()

    def test_root(self):
        """ls без аргументов показывает корень."""
        self.assertEqual(self.shell.run("ls").out, "home  tmp")

    def test_long_format(self):
        """ls -l показывает тип и размер."""
        out = self.shell.run("ls -l /home/user").out
        self.assertEqual(out, f"- {3:>6} bin.dat\nd {0:>6} docs")

    def test_hidden_files(self):
        """Скрытые файлы видны только с ключом -a."""
        self.assertEqual(self.shell.run("ls /home/user").out,
                         "bin.dat  docs")
        self.assertEqual(self.shell.run("ls -a /home/user").out,
                         ".hidden  bin.dat  docs")

    def test_combined_flags(self):
        """Ключи можно объединять: -la."""
        out = self.shell.run("ls -la /home/user").out
        self.assertIn(".hidden", out)
        self.assertTrue(out.startswith("- "))

    def test_file_operand(self):
        """ls для файла печатает его имя."""
        out = self.shell.run("ls /home/user/bin.dat").out
        self.assertEqual(out, "/home/user/bin.dat")

    def test_multiple_paths_have_headers(self):
        """Для нескольких путей выводятся заголовки."""
        out = self.shell.run("ls /tmp /home").out
        self.assertTrue(out.startswith("/tmp:"))
        self.assertIn("/home:\nuser", out)

    def test_missing_path(self):
        """Несуществующий путь - ошибка."""
        result = self.shell.run("ls /nope")
        self.assertFalse(result.ok)
        self.assertIn("/nope", result.out)

    def test_partial_error(self):
        """Ошибка по одному пути не скрывает остальные."""
        result = self.shell.run("ls /tmp /nope")
        self.assertFalse(result.ok)
        self.assertIn("/tmp:", result.out)

    def test_bad_flag(self):
        """Неизвестный ключ - ошибка."""
        self.assertFalse(self.shell.run("ls -z").ok)


class CdTest(unittest.TestCase):
    """Тесты команды cd и приглашения."""

    def setUp(self):
        """Создаёт оболочку."""
        self.shell = build_shell()

    def test_absolute_and_parent(self):
        """Абсолютные пути и .. работают, выше корня не выйти."""
        self.shell.run("cd /home/user/docs")
        self.assertEqual(self.shell.cwd, DOCS)
        self.shell.run("cd ../..")
        self.assertEqual(self.shell.cwd, ["home"])
        self.shell.run("cd ../../..")
        self.assertEqual(self.shell.cwd, [])

    def test_relative(self):
        """Относительные пути считаются от текущей папки."""
        self.shell.run("cd home")
        self.shell.run("cd user/docs")
        self.assertEqual(self.shell.cwd, DOCS)
        self.assertEqual(self.shell.run("ls").out, "a.txt  long.txt")

    def test_no_args_goes_home(self):
        """cd без аргументов ведёт в /home/user."""
        self.shell.run("cd /tmp")
        self.shell.run("cd")
        self.assertEqual(self.shell.cwd, HOME)

    def test_no_args_without_home(self):
        """Если /home/user нет, cd без аргументов ведёт в корень."""
        shell = Shell(VFS(), "> ")
        shell.run("cd")
        self.assertEqual(shell.cwd, [])

    def test_errors(self):
        """Несуществующий путь, файл и лишние аргументы - ошибки."""
        self.assertFalse(self.shell.run("cd /nope").ok)
        self.assertFalse(self.shell.run("cd /home/user/bin.dat").ok)
        self.assertFalse(self.shell.run("cd a b").ok)
        self.assertEqual(self.shell.cwd, [])

    def test_default_prompt_shows_cwd(self):
        """Приглашение по умолчанию показывает текущую папку."""
        shell = build_shell(prompt=None)
        shell.run("cd /tmp")
        self.assertTrue(shell.prompt.endswith(" /tmp]$ "))

    def test_custom_prompt_is_fixed(self):
        """Заданное пользователем приглашение не меняется."""
        self.shell.run("cd /tmp")
        self.assertEqual(self.shell.prompt, "> ")


class HistoryTest(unittest.TestCase):
    """Тесты команды history."""

    def setUp(self):
        """Создаёт оболочку."""
        self.shell = build_shell()

    def test_numbering(self):
        """Команды нумеруются, history видит и саму себя."""
        self.shell.run("ls")
        self.shell.run("cd /tmp")
        lines = self.shell.run("history").out.splitlines()
        self.assertEqual(lines, [f"{1:>5}  ls", f"{2:>5}  cd /tmp",
                                 f"{3:>5}  history"])

    def test_limit(self):
        """history N показывает последние N команд."""
        self.shell.run("ls")
        self.shell.run("cd /tmp")
        out = self.shell.run("history 1").out
        self.assertEqual(out, f"{3:>5}  history 1")

    def test_zero(self):
        """history 0 ничего не показывает."""
        self.shell.run("ls")
        self.assertEqual(self.shell.run("history 0").out, "")

    def test_errors_are_recorded(self):
        """Ошибочные команды тоже попадают в историю."""
        self.shell.run("foo")
        self.assertIn("foo", self.shell.history)

    def test_bad_args(self):
        """Нечисловой аргумент и лишние аргументы - ошибки."""
        self.assertFalse(self.shell.run("history abc").ok)
        self.assertFalse(self.shell.run("history 1 2").ok)


class WhoTest(unittest.TestCase):
    """Тесты команды who."""

    def setUp(self):
        """Создаёт оболочку."""
        self.shell = build_shell()

    def test_who(self):
        """who показывает пользователя и время входа."""
        out = self.shell.run("who").out
        self.assertTrue(out.startswith(self.shell.user))
        self.assertIn("console", out)

    def test_who_q(self):
        """who -q показывает имена и количество."""
        out = self.shell.run("who -q").out
        self.assertTrue(out.endswith("# users=1"))

    def test_who_errors(self):
        """Лишний операнд и неизвестный ключ - ошибки."""
        self.assertFalse(self.shell.run("who now").ok)
        self.assertFalse(self.shell.run("who -z").ok)


class HeadTest(unittest.TestCase):
    """Тесты команды head."""

    def setUp(self):
        """Создаёт оболочку."""
        self.shell = build_shell()
        self.long = "/home/user/docs/long.txt"

    def test_default_ten_lines(self):
        """По умолчанию печатаются первые 10 строк."""
        lines = self.shell.run(f"head {self.long}").out.splitlines()
        self.assertEqual(lines, [str(n) for n in range(1, 11)])

    def test_n_option(self):
        """Ключ -n задаёт число строк (раздельно и слитно)."""
        self.assertEqual(self.shell.run(f"head -n 2 {self.long}").out,
                         "1\n2")
        self.assertEqual(self.shell.run(f"head -n2 {self.long}").out,
                         "1\n2")

    def test_zero_lines(self):
        """head -n 0 ничего не печатает."""
        result = self.shell.run(f"head -n 0 {self.long}")
        self.assertTrue(result.ok)
        self.assertEqual(result.out, "")

    def test_multiple_files_have_headers(self):
        """Для нескольких файлов выводятся заголовки."""
        out = self.shell.run(f"head -n 1 {self.long} /home/user/docs/a.txt")
        self.assertIn(f"==> {self.long} <==", out.out)
        self.assertIn("==> /home/user/docs/a.txt <==\none", out.out)

    def test_binary_is_base64(self):
        """Двоичный файл выводится как base64."""
        out = self.shell.run("head /home/user/bin.dat").out
        self.assertTrue(out.startswith("base64:"))

    def test_relative_path(self):
        """Файл можно указать относительно текущей папки."""
        self.shell.run("cd /home/user/docs")
        self.assertEqual(self.shell.run("head -n 1 a.txt").out, "one")

    def test_errors(self):
        """Все ошибочные варианты вызова дают ok=False."""
        bad = ["head", "head /nope.txt", "head /home", "head -n x /tmp",
               "head -n", "head -z /tmp"]
        for line in bad:
            with self.subTest(line=line):
                self.assertFalse(self.shell.run(line).ok)


class TouchTest(unittest.TestCase):
    """Тесты команды touch."""

    def setUp(self):
        """Создаёт оболочку."""
        self.shell = build_shell()

    def test_creates_empty_file(self):
        """touch создаёт пустой файл, который виден в ls."""
        self.assertTrue(self.shell.run("touch /tmp/a.txt").ok)
        node = self.shell.vfs.get(["tmp", "a.txt"])
        self.assertFalse(node.is_dir)
        self.assertEqual(node.data, b"")
        self.assertEqual(self.shell.run("ls /tmp").out, "a.txt")

    def test_relative_path(self):
        """Путь считается от текущей папки."""
        self.shell.run("cd /tmp")
        self.shell.run("touch b.txt")
        self.assertIsNotNone(self.shell.vfs.get(["tmp", "b.txt"]))

    def test_multiple_files(self):
        """touch создаёт сразу несколько файлов."""
        self.shell.run("touch /tmp/x /tmp/y")
        self.assertEqual(self.shell.run("ls /tmp").out, "x  y")

    def test_existing_file_unchanged(self):
        """Существующий файл не изменяется."""
        self.shell.run("touch /home/user/docs/a.txt")
        node = self.shell.vfs.get(DOCS + ["a.txt"])
        self.assertEqual(node.data, b"one\ntwo\n")

    def test_existing_dir_is_ok(self):
        """touch для существующей папки не вызывает ошибки."""
        self.assertTrue(self.shell.run("touch /tmp").ok)

    def test_errors(self):
        """Неверные варианты вызова дают ok=False."""
        bad = ["touch", "touch /nope/x", "touch /home/user/bin.dat/x",
               "touch -z x"]
        for line in bad:
            with self.subTest(line=line):
                self.assertFalse(self.shell.run(line).ok)

    def test_partial_error(self):
        """Ошибка по одному файлу не мешает создать остальные."""
        result = self.shell.run("touch /nope/x /tmp/ok")
        self.assertFalse(result.ok)
        self.assertIsNotNone(self.shell.vfs.get(["tmp", "ok"]))


class RmTest(unittest.TestCase):
    """Тесты команды rm."""

    def setUp(self):
        """Создаёт оболочку."""
        self.shell = build_shell()

    def test_removes_file(self):
        """rm удаляет файл."""
        self.assertTrue(self.shell.run("rm /home/user/bin.dat").ok)
        self.assertIsNone(self.shell.vfs.get(HOME + ["bin.dat"]))
        self.assertEqual(self.shell.run("ls /home/user").out, "docs")

    def test_dir_needs_recursive(self):
        """Папку без -r удалить нельзя."""
        result = self.shell.run("rm /home/user/docs")
        self.assertFalse(result.ok)
        self.assertIsNotNone(self.shell.vfs.get(DOCS))

    def test_recursive_removes_tree(self):
        """rm -r удаляет папку вместе с содержимым."""
        self.assertTrue(self.shell.run("rm -r /home/user/docs").ok)
        self.assertIsNone(self.shell.vfs.get(DOCS))
        self.assertIsNone(self.shell.vfs.get(DOCS + ["a.txt"]))

    def test_combined_flags(self):
        """Ключи объединяются: -rf."""
        self.assertTrue(self.shell.run("rm -rf /tmp /nope").ok)
        self.assertIsNone(self.shell.vfs.get(["tmp"]))

    def test_force_ignores_missing(self):
        """Ключ -f подавляет ошибку для несуществующего пути."""
        self.assertTrue(self.shell.run("rm -f /nope").ok)
        self.assertFalse(self.shell.run("rm /nope").ok)

    def test_relative_path(self):
        """Путь считается от текущей папки."""
        self.shell.run("cd /home/user/docs")
        self.shell.run("rm a.txt")
        self.assertEqual(self.shell.run("ls").out, "long.txt")

    def test_protects_cwd_and_parents(self):
        """Нельзя удалить текущую папку, её родителей и корень."""
        self.shell.run("cd /home/user/docs")
        for line in ["rm -r .", "rm -r ..", "rm -r /home", "rm -r /"]:
            with self.subTest(line=line):
                self.assertFalse(self.shell.run(line).ok)
        self.assertIsNotNone(self.shell.vfs.get(DOCS))

    def test_sibling_can_be_removed(self):
        """Соседние папки удалять можно."""
        self.shell.run("cd /home/user/docs")
        self.assertTrue(self.shell.run("rm -r /tmp").ok)

    def test_partial_error(self):
        """Ошибка по одному пути не мешает удалить остальные."""
        result = self.shell.run("rm /nope /home/user/bin.dat")
        self.assertFalse(result.ok)
        self.assertIsNone(self.shell.vfs.get(HOME + ["bin.dat"]))

    def test_errors(self):
        """Отсутствие операнда и неверный ключ - ошибки."""
        self.assertFalse(self.shell.run("rm").ok)
        self.assertFalse(self.shell.run("rm -z x").ok)


class ArchiveUntouchedTest(unittest.TestCase):
    """Изменения VFS не должны затрагивать исходный ZIP-архив."""

    def test_zip_not_modified(self):
        """После touch и rm архив не меняется и ничего не распаковано."""
        with tempfile.TemporaryDirectory() as directory:
            files = {"a/b.txt": "x", "c.txt": "y"}
            path = make_zip(directory, "t.zip", files)
            with open(path, "rb") as file:
                before = file.read()
            shell = Shell(VFS.from_zip(path), "> ")
            shell.run("touch /new.txt")
            shell.run("rm -r /a")
            with open(path, "rb") as file:
                after = file.read()
            self.assertEqual(before, after)
            self.assertEqual(os.listdir(directory), ["t.zip"])
            self.assertIsNone(shell.vfs.get(["a"]))
            self.assertIsNotNone(shell.vfs.get(["new.txt"]))
            self.assertIsNotNone(VFS.from_zip(path).get(["a", "b.txt"]))


if __name__ == "__main__":
    unittest.main()
