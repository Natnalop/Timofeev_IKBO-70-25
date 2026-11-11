@echo off
rem Запуск эмулятора: run.bat [--vfs ZIP] [--prompt STR] [--script FILE]
python "%~dp0src\emulator.py" %*
