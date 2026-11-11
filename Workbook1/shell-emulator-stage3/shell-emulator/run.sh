#!/bin/sh
# Запуск эмулятора: ./run.sh [--vfs ZIP] [--prompt STR] [--script FILE]
exec python3 "$(dirname "$0")/src/emulator.py" "$@"
