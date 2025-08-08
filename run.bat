@echo off
chcp 65001 >nul
echo Starting PyQt Vehicle Monitor Editor...
call venv\Scripts\activate.bat
python main.py
call deactivate