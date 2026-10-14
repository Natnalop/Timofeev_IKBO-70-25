@echo off
chcp 65001 >nul
rem Тест этапа 5 (Windows). Запуск из корня репозитория.
set SAMPLES=tests\vfs_samples
set SCRIPT=tests\start_stage5.txt

python tests\make_vfs.py

echo === Модульные тесты ===
set PYTHONPATH=src
python -m unittest discover -s tests

copy /y %SAMPLES%\deep.zip %SAMPLES%\deep.orig >nul
echo.& echo === deep.zip, свой prompt ===
python src\emulator.py --headless --vfs %SAMPLES%\deep.zip --prompt "deep# " --script %SCRIPT%
echo.& echo === deep.zip, приглашение с текущей папкой ===
python src\emulator.py --headless --vfs %SAMPLES%\deep.zip --script %SCRIPT%
echo.& echo === several.zip ===
python src\emulator.py --headless --vfs %SAMPLES%\several.zip --prompt "[several]$ " --script %SCRIPT%
echo.& echo === VFS по умолчанию ===
python src\emulator.py --headless --script %SCRIPT%

echo.
fc /b %SAMPLES%\deep.zip %SAMPLES%\deep.orig >nul && (echo === Архив deep.zip не изменён: правки были только в памяти ===) || (echo === ОШИБКА: архив deep.zip изменился ===)
del %SAMPLES%\deep.orig
