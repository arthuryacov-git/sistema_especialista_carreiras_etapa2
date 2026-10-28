@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -m unittest discover -s tests -v
) else (
  python -m unittest discover -s tests -v
)
pause
