@echo off
chcp 65001 >nul
echo ========================================
echo PyQt Vehicle Monitor Editor - Setup
echo ========================================
echo.

REM Create virtual environment
echo Creating virtual environment...
if exist venv (
    echo Removing existing venv...
    rmdir /s /q venv
)
python -m venv venv

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install packages
echo.
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ========================================
echo Setup completed!
echo ========================================
echo.
echo Usage:
echo   run.bat - Start PyQt Vehicle Monitor Editor
echo.
pause
deactivate