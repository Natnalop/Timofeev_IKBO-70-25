import base64
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "vfs_samples")
BINARY_B64 = "AAECAwT//vw="
LONG_LINES = 15
LONG_TEXT = "".join(f"строка {n}\n" for n in range(1, LONG_LINES + 1))


def write_zip(name, files):
    """Создаёт архив ``name`` из словаря ``{путь: содержимое}``."""
    path = os.path.join(OUT_DIR, name)
    with zipfile.ZipFile(path, "w") as archive:
        for entry, content in files.items():
            archive.writestr(entry, content)


def write_broken(name):
    """Создаёт файл, который не является ZIP-архивом."""
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as file:
        file.write("это не zip-архив, а обычный текст\n")


def make_all():
    """Создаёт все тестовые архивы."""
    os.makedirs(OUT_DIR, exist_ok=True)
    write_zip("minimal.zip", {"hello.txt": "Привет из минимальной VFS\n"})
    write_zip("several.zip", {
        "a.txt": "файл A\n",
        "b.txt": "файл B\nвторая строка\n",
        "notes.md": "# Заметки\n",
        "data.bin": base64.b64decode(BINARY_B64),
    })
    write_zip("deep.zip", {
        "home/user/docs/work/report.txt": "отчёт\n",
        "home/user/docs/work/todo.txt": "1. сдать этап 3\n",
        "home/user/docs/notes.txt": "заметки\n",
        "home/user/music/": "",
        "etc/config/app/settings.ini": "[main]\nlevel=3\n",
        "home/user/docs/long.txt": LONG_TEXT,
        "home/user/.profile": "export PS1='$ '\n",
        "home/user/data.bin": base64.b64decode(BINARY_B64),
        "readme.txt": "корень\n",
    })
    write_broken("broken.zip")
    print("Готово:", ", ".join(sorted(os.listdir(OUT_DIR))))


if __name__ == "__main__":
    make_all()
