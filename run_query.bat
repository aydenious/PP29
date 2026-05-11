@echo off
REM ============================================================
REM  PP29 Query Tool
REM  Look up items, compare dates, find changes.
REM
REM  Prerequisites:
REM    - Run setup.bat first (once) to install Python + dependencies
REM    - At least one daily run completed (data in SQLite)
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
echo   PP29 Query Tool
echo ========================================
echo.
echo   [1] Look up an item across all dates
echo   [2] Compare an item between two dates
echo   [3] Show top changes across all dates
echo   [4] Show all dates summary
echo.

set /p choice="Enter choice (1-4): "

if "%choice%"=="1" goto :lookup
if "%choice%"=="2" goto :compare
if "%choice%"=="3" goto :topchanges
if "%choice%"=="4" goto :summary
echo Invalid choice.
pause
exit /b

:lookup
set /p item="Enter item code: "
"%PYTHON_EXE%" src\query.py --item %item%
pause
exit /b

:compare
set /p item="Enter item code: "
set /p d1="Enter first date (YYYYMMDD): "
set /p d2="Enter second date (YYYYMMDD): "
"%PYTHON_EXE%" src\query.py --item %item% --dates %d1%,%d2%
pause
exit /b

:topchanges
set /p limit="How many top movers to show? [20]: "
if "%limit%"=="" set limit=20
"%PYTHON_EXE%" src\query.py --top-changes --limit %limit%
pause
exit /b

:summary
"%PYTHON_EXE%" src\query.py --dates-summary
pause
exit /b
