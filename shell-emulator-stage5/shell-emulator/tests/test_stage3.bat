@echo off
chcp 65001 >nul
rem Тест этапа 3 (Windows). Запуск из корня репозитория.
set SAMPLES=tests\vfs_samples
set SCRIPT=tests\start_all.txt

python tests\make_vfs.py

echo === Модульные тесты ===
set PYTHONPATH=src
python -m unittest discover -s tests

echo.& echo === VFS по умолчанию ===
python src\emulator.py --headless --script %SCRIPT%
echo.& echo === minimal.zip ===
python src\emulator.py --headless --vfs %SAMPLES%\minimal.zip --prompt "min> " --script %SCRIPT%
echo.& echo === several.zip ===
python src\emulator.py --headless --vfs %SAMPLES%\several.zip --prompt "[several]$ " --script %SCRIPT%
echo.& echo === deep.zip ===
python src\emulator.py --headless --vfs %SAMPLES%\deep.zip --prompt "deep# " --script %SCRIPT%
echo.& echo === ОШИБКА: неверный формат VFS ===
python src\emulator.py --headless --vfs %SAMPLES%\broken.zip
echo.& echo === ОШИБКА: VFS не найдена ===
python src\emulator.py --headless --vfs %SAMPLES%\net_takogo.zip
echo.& echo === ОШИБКА: скрипт не найден ===
python src\emulator.py --headless --script tests\net_takogo.txt
