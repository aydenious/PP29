@echo off
REM fix_pth.bat — Repair a broken Python embeddable ._pth file
REM Run this if you get "Failed to import encodings module"
cd /d "%~dp0"

echo.
echo ========================================
echo   PP29 - Fix Python ._pth configuration
echo ========================================
echo.

REM Find files
set "PTH_FILE="
for %%f in (python3*._pth) do set "PTH_FILE=%%f"
set "ZIP_FILE="
for %%f in (python3*.zip) do set "ZIP_FILE=%%f"

if not defined PTH_FILE (
    echo ERROR: No ._pth file found. Is Python extracted?
    pause
    exit /b 1
)
if not defined ZIP_FILE (
    echo ERROR: No python3xx.zip found. Python stdlib missing.
    pause
    exit /b 1
)

echo   ._pth file: %PTH_FILE%
echo   Stdlib zip: %ZIP_FILE%

REM Backup the current ._pth
copy "%PTH_FILE%" "%PTH_FILE%.backup" >nul

REM Write correct ._pth content
(
    echo %ZIP_FILE%
    echo .
    echo Lib\site-packages
    echo import site
) > "%PTH_FILE%"

echo.
echo   Wrote new %PTH_FILE%:
type "%PTH_FILE%"
echo.

REM Test
echo   Testing python...
python.exe -c "print('Python OK')" 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   FAILED. Restoring backup...
    copy "%PTH_FILE%.backup" "%PTH_FILE%" >nul
    echo.
    echo   Something else is wrong. Check that %ZIP_FILE% exists
    echo   and is not corrupted. Try re-extracting the embeddable zip.
    pause
    exit /b 1
)

del "%PTH_FILE%.backup" 2>nul
echo.
echo   Success! Now re-run setup.bat to continue.
pause
