@echo off
chcp 65001 >nul
rem Тест этапа 5 (Windows). Запуск из корня репозитория.
set SAMPLES=tests\vfs_samples
set SCRIPT=tests\start_stage5.txt

python tests\make_vfs.py

set PYTHONPATH=src
python -m unittest discover -s tests

copy /y %SAMPLES%\deep.zip %SAMPLES%\deep.orig >nul
python src\emulator.py --headless --vfs %SAMPLES%\deep.zip --prompt "deep# " --script %SCRIPT%
python src\emulator.py --headless --vfs %SAMPLES%\deep.zip --script %SCRIPT%
python src\emulator.py --headless --vfs %SAMPLES%\several.zip --prompt "[several]$ " --script %SCRIPT%
python src\emulator.py --headless --script %SCRIPT%

echo.
fc /b %SAMPLES%\deep.zip %SAMPLES%\deep.orig >nul
del %SAMPLES%\deep.orig
