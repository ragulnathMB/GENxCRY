@echo off
echo Starting GENxCRY - AI Dataset Generator
echo By RN Software
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Install requirements if needed
echo Installing/checking requirements...
pip install -r requirements.txt

REM Start the application
echo Starting GENxCRY...
python main.py

pause
