@echo off
REM ============================================================
REM  PP29 Daily Purchase Plan Generator
REM  Double-click to run. Replaces MS Access refresh.
REM
REM  Prerequisites:
REM    - Run setup.bat first (once) to install Python + dependencies
REM    - config.json configured with your SAP download path
REM  ============================================================

cd /d "%~dp0"

REM Find the Python executable (handles any embeddable version)
set PYTHON_EXE=
for %%f in (python.exe) do set PYTHON_EXE=%%~dpnx$PATH:f
if exist "%~dp0python.exe" set PYTHON_EXE=%~dp0python.exe

if not defined PYTHON_EXE (
    echo ERROR: python.exe not found. Run setup.bat first.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   PP29 Daily Purchase Plan Generator
echo ========================================
echo.

REM Use today's date automatically
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set datetime=%%I
if not defined datetime (
    REM Fallback: use PowerShell to get date
    for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set datetime=%%I
)
set TODAY=%datetime:~0,8%
echo Processing date: %TODAY%
echo.

"%PYTHON_EXE%" src\daily.py --date %TODAY%

echo.
echo ========================================
echo   Done! Check output\daily\
echo ========================================
pause
