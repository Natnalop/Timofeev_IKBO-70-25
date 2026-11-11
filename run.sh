#!/bin/sh
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export PYTHONUTF8=1
exec python3 "$SCRIPT_DIR/src/main.py" "$@"
