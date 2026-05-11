@echo off
REM ============================================================
REM  PP29 Multi-date Consolidation
REM  Combines all daily Excel files into a comparison workbook.
REM
REM  Prerequisites:
REM    - Run setup.bat first (once) to install Python + dependencies
REM    - config.json configured with paths
REM    - At least 2 daily runs completed
REM  ============================================================

cd /d "%~dp0"

set PYTHON_EXE=
if exist "%~dp0python.exe" set PYTHON_EXE=%~dp0python.exe

if not defined PYTHON_EXE (
    echo ERROR: python.exe not found. Run setup.bat first.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   PP29 Consolidation - All Dates
echo ========================================
echo.
echo Choose data source:
echo   [1] SQLite database ^(recommended^)
echo   [2] Daily .xlsx files ^(output\daily^)
echo   [3] Legacy Access .xls files ^(network drive^)
echo.

set /p choice="Enter 1, 2, or 3: "

if "%choice%"=="1" (
    "%PYTHON_EXE%" src\consolidate.py --source db
) else if "%choice%"=="2" (
    "%PYTHON_EXE%" src\consolidate.py --source daily
) else if "%choice%"=="3" (
    "%PYTHON_EXE%" src\consolidate.py --source excel
) else (
    echo Invalid choice.
)

echo.
echo ========================================
echo   Done! Check output\consolidated\
echo ========================================
pause
