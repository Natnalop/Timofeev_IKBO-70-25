"""Вспомогательные функции для тестов."""
import os
import zipfile


def make_zip(directory, name, files):
    """Создаёт в папке ``directory`` архив и возвращает путь к нему."""
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
