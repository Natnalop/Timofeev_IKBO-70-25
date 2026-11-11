#!/bin/sh
# Тест этапа 4: команды ls, cd, history, who, head на разных VFS.
# Запуск из корня репозитория: sh tests/test_stage4.sh
PY=${PY:-python3}
SAMPLES=tests/vfs_samples
SCRIPT=tests/start_stage4.txt

run() {
    echo
    $PY src/emulator.py --headless "$@"
}

$PY tests/make_vfs.py

PYTHONPATH=src $PY -m unittest discover -s tests

run --vfs $SAMPLES/deep.zip --prompt "deep# " --script $SCRIPT
run --vfs $SAMPLES/deep.zip --script $SCRIPT
run --vfs $SAMPLES/several.zip --prompt "[several]$ " --script $SCRIPT
run --script $SCRIPT
