@echo off
chcp 65001 >nul
:menu
echo ========================================
echo Framework Comparison - Menu
echo ========================================
echo.
echo 1. Run PyQt Vehicle Monitor (Main)
echo 2. Run Flet Image Editor
echo 3. Setup All Frameworks
echo 4. Show Documentation
echo 5. Exit
echo.
set /p choice=Please select (1-5): 

if "%choice%"=="1" goto run_pyqt
if "%choice%"=="2" goto run_flet
if "%choice%"=="3" goto setup_all
if "%choice%"=="4" goto docs
if "%choice%"=="5" exit /b

:run_pyqt
echo.
echo Running PyQt Vehicle Monitor (Main)...
if not exist venv (
    echo Virtual environment not found. Please run setup first.
    pause
    goto menu
)
call venv\Scripts\activate.bat
python main.py
call deactivate
pause
goto menu

:run_flet
echo.
echo Running Flet Image Editor...
cd framework_comparison\flet
if not exist venv (
    echo Virtual environment not found. Please run setup first.
    cd ..\..
    pause
    goto menu
)
call venv\Scripts\activate.bat
python image_editor.py
call deactivate
cd ..\..
pause
goto menu

:setup_all
echo.
echo Setting up all frameworks...
echo.
echo [1/2] Setting up PyQt version (Main)...
if exist venv (
    echo Removing existing PyQt venv...
    rmdir /s /q venv
)
echo Creating PyQt virtual environment...
python -m venv venv
echo Activating PyQt environment...
call venv\Scripts\activate.bat
echo Installing PyQt dependencies...
pip install --upgrade pip
pip install -r requirements.txt
call deactivate
echo.
echo [2/2] Setting up Flet version...
cd framework_comparison\flet
if exist venv (
    echo Removing existing Flet venv...
    rmdir /s /q venv
)
echo Creating Flet virtual environment...
python -m venv venv
echo Activating Flet environment...
call venv\Scripts\activate.bat
echo Installing Flet dependencies...
pip install --upgrade pip
pip install -r requirements.txt
call deactivate
cd ..\..
echo.
echo All setup completed!
pause
goto menu

:docs
echo.
echo Documentation files:
echo - Comparison: framework_comparison\docs\comparison.md
echo - Setup Guide: framework_comparison\docs\VENV_GUIDE.md
echo.
pause
goto menu