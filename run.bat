@echo off
setlocal
set PYTHONUTF8=1
python "%~dp0src\main.py" %*
exit /b %errorlevel%
