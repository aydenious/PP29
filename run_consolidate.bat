@echo off
REM ============================================================
REM  PP29 Multi-date Consolidation
REM  Combines all daily Excel files into a comparison workbook.
REM  ============================================================

cd /d "%~dp0"

echo.
echo ========================================
echo   PP29 Consolidation - All Dates
echo ========================================
echo.

python.exe src\consolidate.py --source excel

echo.
echo ========================================
echo   Done! Check output\consolidated\
echo ========================================
pause
