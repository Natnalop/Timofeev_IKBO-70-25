"""Конфигурация эмулятора: параметры командной строки и загрузка VFS."""
import argparse

from vfs import VFS, VFSError


def parse_args(argv=None):
    """Разбирает параметры командной строки."""
    parser = argparse.ArgumentParser(description="Эмулятор оболочки UNIX")
    parser.add_argument("--vfs", help="путь к ZIP-архиву с VFS")
    parser.add_argument("--prompt", help="приглашение к вводу")
    parser.add_argument("--script", help="путь к стартовому скрипту")
    parser.add_argument("--headless", action="store_true",
                        help="консольный режим без GUI")
    return parser.parse_args(argv)


def debug_params(args):
    """Возвращает отладочный вывод всех заданных параметров."""
    return "\n".join([
        "[debug] параметры запуска:",
        f"[debug]   vfs    = {args.vfs}",
        f"[debug]   prompt = {args.prompt}",
        f"[debug]   script = {args.script}",
    ])


def load_vfs(path, write):
    """Загружает VFS; при ошибке сообщает о ней и возвращает None."""
    if not path:
        return VFS.default()
    try:
        return VFS.from_zip(path)
    except VFSError as err:
        write(f"[vfs] ошибка загрузки: {err}")
        return None
