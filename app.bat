@echo off
chcp 65001 >nul
echo Starting Vehicle Monitor Application...
call venv\Scripts\activate.bat
python app.py
call deactivate