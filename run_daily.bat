@echo off
REM ============================================================
REM  PP29 Daily Purchase Plan Generator
REM  Double-click to run. Replaces MS Access refresh.
REM
REM  Prerequisites:
REM    - PP29_Tool folder copied to your machine or network drive
REM    - config.json configured with your SAP download path
REM  ============================================================

cd /d "%~dp0"

echo.
echo ========================================
echo   PP29 Daily Purchase Plan Generator
echo ========================================
echo.

REM Use today's date automatically
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TODAY=%datetime:~0,8%
echo Processing date: %TODAY%
echo.

python.exe src\daily.py --date %TODAY%

echo.
echo ========================================
echo   Done! Check the output folder.
echo ========================================
pause
