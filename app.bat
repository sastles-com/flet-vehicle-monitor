@echo off
chcp 65001 >nul
echo Starting Vehicle Monitor Modern Application...

REM Check if venv exists, create if not
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
echo Installing/updating dependencies...
pip install -r requirements.txt

echo Starting application...
REM Note: CONFIG->EDIT cursor change feature implemented (log only)

REM Resolve user's Desktop dynamically and pass to Python
set "DEFAULT_DIR="
for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "[Environment]::GetFolderPath('Desktop')"`) do set "DEFAULT_DIR=%%D"
REM Fallback if PowerShell is unavailable
if not defined DEFAULT_DIR (
    if defined USERPROFILE (
        set "DEFAULT_DIR=%USERPROFILE%\Desktop"
    ) else (
        set "DEFAULT_DIR=."
    )
)

echo Using DEFAULT_DIR=%DEFAULT_DIR%
python edit_mode.py --no-dialog --default-dir "%DEFAULT_DIR%"
call deactivate
