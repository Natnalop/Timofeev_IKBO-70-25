@echo off
chcp 65001 >nul
rem Тест этапа 3 (Windows). Запуск из корня репозитория.
set SAMPLES=tests\vfs_samples
set SCRIPT=tests\start_all.txt

python tests\make_vfs.py

set PYTHONPATH=src
python -m unittest discover -s tests

python src\emulator.py --headless --script %SCRIPT%
python src\emulator.py --headless --vfs %SAMPLES%\minimal.zip --prompt "min> " --script %SCRIPT%
python src\emulator.py --headless --vfs %SAMPLES%\several.zip --prompt "[several]$ " --script %SCRIPT%
python src\emulator.py --headless --vfs %SAMPLES%\deep.zip --prompt "deep# " --script %SCRIPT%
python src\emulator.py --headless --vfs %SAMPLES%\broken.zip
python src\emulator.py --headless --vfs %SAMPLES%\net_takogo.zip
python src\emulator.py --headless --script tests\net_takogo.txt
