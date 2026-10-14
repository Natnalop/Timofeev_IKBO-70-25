#!/bin/sh
# Тест этапа 3: разные VFS и параметры командной строки.
# Запуск из корня репозитория: sh tests/test_stage3.sh
PY=${PY:-python3}
SAMPLES=tests/vfs_samples
SCRIPT=tests/start_all.txt

run() {
    echo
    echo "=== $* ==="
    $PY src/emulator.py --headless "$@"
}

$PY tests/make_vfs.py

echo "=== Модульные тесты ==="
PYTHONPATH=src $PY -m unittest discover -s tests

run --script $SCRIPT
run --vfs $SAMPLES/minimal.zip --prompt "min> " --script $SCRIPT
run --vfs $SAMPLES/several.zip --prompt "[several]$ " --script $SCRIPT
run --vfs $SAMPLES/deep.zip --prompt "deep# " --script $SCRIPT

echo
echo "=== ОШИБКИ ЗАГРУЗКИ VFS ==="
run --vfs $SAMPLES/broken.zip
run --vfs $SAMPLES/net_takogo.zip

echo
echo "=== ОШИБКА СТАРТОВОГО СКРИПТА ==="
run --script tests/net_takogo.txt
