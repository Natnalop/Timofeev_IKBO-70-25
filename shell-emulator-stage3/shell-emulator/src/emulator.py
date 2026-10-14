"""Точка входа эмулятора оболочки UNIX (этапы 1-3).

Запуск: ``python src/emulator.py [--vfs ZIP] [--prompt STR]
[--script FILE] [--headless]``.
"""
import sys

from config import debug_params, load_vfs, parse_args
from shell import Shell


def repl(shell):
    """Интерактивный цикл консольного режима; возвращает код выхода."""
    while True:
        try:
            line = input(shell.prompt)
        except EOFError:
            return 0
        result = shell.run(line)
        if result.out:
            print(result.out)
        if result.should_exit:
            return 0


def run_headless(args):
    """Консольный режим: выполняет скрипт или читает ввод с клавиатуры."""
    print(debug_params(args))
    vfs = load_vfs(args.vfs, print)
    if vfs is None:
        return 1
    shell = Shell(vfs, args.prompt)
    if args.script:
        shell.run_script(args.script, print)
        return 0
    return repl(shell)


def main(argv=None):
    """Запускает эмулятор в графическом или консольном режиме."""
    args = parse_args(argv)
    if args.headless:
        return run_headless(args)
    from gui import run_gui
    return run_gui(args)


if __name__ == "__main__":
    sys.exit(main())
