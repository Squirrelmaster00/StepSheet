@echo off
cd /d "%~dp0"
where py >nul 2>nul && (py -m stepsheet %*) || (python -m stepsheet %*)
pause
