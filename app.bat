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
python app_modern.py
call deactivate