@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo   PP29 Portable Runtime Setup
echo   This installs Python + dependencies into this folder.
echo   No admin rights needed. No system-wide changes.
echo   Internet connection required for download.
echo ============================================================
echo.

REM ============================================================
REM  STEP 0: Check if already set up
REM ============================================================

if exist "python.exe" (
    echo python.exe already exists in this folder.
    choice /c yn /m "Re-run setup anyway?"
    if errorlevel 2 goto :done
    if errorlevel 1 goto :start_download
)

REM ============================================================
REM  STEP 1: Download Python embeddable
REM ============================================================

:start_download

REM Try multiple Python versions (newest first)
set "PY_VERSIONS=3.13.9 3.13.8 3.13.7 3.13.6 3.13.5 3.13.4 3.13.3 3.13.2 3.13.1 3.13.0 3.12.9 3.12.8 3.12.7"
set "DOWNLOADED="

echo.
echo Step 1: Downloading Python embeddable...
echo.

for %%v in (%PY_VERSIONS%) do (
    if not defined DOWNLOADED (
        set "URL=https://www.python.org/ftp/python/%%v/python-%%v-embed-amd64.zip"
        set "ZIP=python-%%v-embed-amd64.zip"

        echo Trying: !URL!

        REM Try PowerShell first (built into Windows)
        powershell -NoProfile -Command "& { try { Invoke-WebRequest -Uri '!URL!' -OutFile '!ZIP!' -UseBasicParsing; exit 0 } catch { exit 1 } }" >nul 2>&1
        if !errorlevel! equ 0 (
            if exist "!ZIP!" (
                echo   Downloaded successfully.
                set "DOWNLOADED=!ZIP!"
                set "PY_VER=%%v"
            )
        )

        REM Fallback: try curl (available in modern Windows 10/11)
        if not defined DOWNLOADED (
            curl -s -o "!ZIP!" "!URL!" 2>nul
            if exist "!ZIP!" (
                powershell -NoProfile -Command "if ((Get-Item '!ZIP!').Length -gt 100000) { exit 0 } else { exit 1 }" >nul 2>&1
                if !errorlevel! equ 0 (
                    echo   Downloaded successfully.
                    set "DOWNLOADED=!ZIP!"
                    set "PY_VER=%%v"
                ) else (
                    del "!ZIP!" 2>nul
                )
            )
        )
    )
)

if not defined DOWNLOADED (
    echo.
    echo ============================================================
    echo   DOWNLOAD FAILED
    echo ============================================================
    echo.
    echo Could not download Python automatically. This may be due to:
    echo   - No internet access
    echo   - Company firewall blocking python.org
    echo   - Corporate proxy not configured
    echo.
    echo MANUAL SETUP:
    echo   1. On a machine with internet, download from:
    echo      https://www.python.org/downloads/windows/
    echo   2. Choose "Windows embeddable package (64-bit)" for Python 3.13
    echo   3. Place the zip file in this folder: %~dp0
    echo   4. Re-run this setup.bat
    echo.
    pause
    exit /b 1
)

REM ============================================================
REM  STEP 2: Extract Python embeddable
REM ============================================================

echo.
echo Step 2: Extracting Python...
powershell -NoProfile -Command "Expand-Archive -Force -Path '%DOWNLOADED%' -DestinationPath '%~dp0'"
if %errorlevel% neq 0 (
    echo ERROR: Failed to extract Python archive.
    pause
    exit /b 1
)
del "%DOWNLOADED%" 2>nul
echo   Done.

REM ============================================================
REM  STEP 3: Configure ._pth file for site-packages
REM ============================================================

echo.
echo Step 3: Configuring Python path...

REM Find the ._pth file
set "PTH_FILE="
for %%f in (python3*._pth) do set "PTH_FILE=%%f"

if not defined PTH_FILE (
    echo ERROR: Could not find python3*._pth file.
    pause
    exit /b 1
)

echo   Found: %PTH_FILE%

REM Write the correct _pth configuration
(
    echo python3!PY_VER:~0,1!!PY_VER:~2,2!.zip
    echo .
    echo Lib\site-packages
    echo.
    echo # Uncomment to run site.main^(^) automatically
    echo import site
) > "%PTH_FILE%"

echo   Configured %PTH_FILE% for site-packages support.

REM ============================================================
REM  STEP 4: Install pip
REM ============================================================

echo.
echo Step 4: Installing pip...

REM Download get-pip.py
powershell -NoProfile -Command "& { try { Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py' -UseBasicParsing; exit 0 } catch { exit 1 } }" >nul 2>&1
if not exist get-pip.py (
    curl -s -o get-pip.py https://bootstrap.pypa.io/get-pip.py 2>nul
)
if not exist get-pip.py (
    echo ERROR: Could not download get-pip.py.
    pause
    exit /b 1
)

python.exe get-pip.py --no-warn-script-location
if %errorlevel% neq 0 (
    echo ERROR: pip installation failed.
    pause
    exit /b 1
)
del get-pip.py 2>nul
echo   pip installed.

REM ============================================================
REM  STEP 5: Install required Python packages
REM ============================================================

echo.
echo Step 5: Installing openpyxl and xlrd...
python.exe -m pip install --no-warn-script-location openpyxl xlrd
if %errorlevel% neq 0 (
    echo ERROR: Package installation failed.
    echo Check internet connection and try again.
    pause
    exit /b 1
)
echo   Packages installed.

REM ============================================================
REM  STEP 6: Verify installation
REM ============================================================

echo.
echo Step 6: Verifying installation...

python.exe -c "import openpyxl; print('  openpyxl', openpyxl.__version__)" 2>nul || (
    echo   WARNING: openpyxl import failed
)
python.exe -c "import xlrd; print('  xlrd', xlrd.__version__)" 2>nul || (
    echo   WARNING: xlrd import failed
)
python.exe -c "import sqlite3; print('  sqlite3 built-in')" 2>nul || (
    echo   WARNING: sqlite3 import failed
)

REM ============================================================
REM  STEP 7: Create config.json if it doesn't exist
REM ============================================================

echo.
echo Step 7: Checking configuration...

if not exist config.json (
    echo   config.json not found. Copying from template...
    copy config.example.json config.json >nul
    echo.
    echo   ^^!^^!^^! IMPORTANT ^^!^^!^^!
    echo   Edit config.json and set these paths for your environment:
    echo     - sap_input_path: Where SAP drops the 13 daily .txt files
    echo     - daily_output_path: Where to save generated Excel files
    echo     - consolidated_output_path: Where to save combined workbooks
    echo   ^^!^^!^^!^^!^^!^^!^^!^^!^^!^^!^^!^^!^^!^^!^^!^^!^^!^^!^^!
) else (
    echo   config.json already exists.
)

REM ============================================================
REM  DONE
REM ============================================================

echo.
echo ============================================================
echo   SETUP COMPLETE
echo ============================================================
echo.
echo   PP29_Tool is ready to use:
echo.
echo     run_daily.bat       - Generate today's Purchase Plan
echo     run_consolidate.bat  - Compare all dates
echo.
echo   Make sure you've edited config.json with your paths!
echo ============================================================

:done
pause
endlocal
