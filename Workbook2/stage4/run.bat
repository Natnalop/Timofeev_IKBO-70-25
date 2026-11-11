@echo off
setlocal
set PYTHONUTF8=1
python "%~dp0depgraph.py" %*
exit /b %errorlevel%
