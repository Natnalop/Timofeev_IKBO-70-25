#!/bin/sh
# Тест этапа 5: команды touch и rm, изменения только в памяти.
# Запуск из корня репозитория: sh tests/test_stage5.sh
PY=${PY:-python3}
SAMPLES=tests/vfs_samples
SCRIPT=tests/start_stage5.txt

run() {
    echo
    $PY src/emulator.py --headless "$@"
}

$PY tests/make_vfs.py

PYTHONPATH=src $PY -m unittest discover -s tests

BEFORE=$(cksum < $SAMPLES/deep.zip)
run --vfs $SAMPLES/deep.zip --prompt "deep# " --script $SCRIPT
run --vfs $SAMPLES/deep.zip --script $SCRIPT
run --vfs $SAMPLES/several.zip --prompt "[several]$ " --script $SCRIPT
run --script $SCRIPT
AFTER=$(cksum < $SAMPLES/deep.zip)

echo
if [ "$BEFORE" = "$AFTER" ]; then
    :
else
    exit 1
fi
