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

REM Use the directory containing this bat file as DEFAULT_DIR
set "DEFAULT_DIR=%~dp0"
REM Strip trailing backslash
if "%DEFAULT_DIR:~-1%"=="\" set "DEFAULT_DIR=%DEFAULT_DIR:~0,-1%"

echo Using DEFAULT_DIR=%DEFAULT_DIR%
python edit_mode.py --no-dialog --default-dir "%DEFAULT_DIR%"
call deactivate
