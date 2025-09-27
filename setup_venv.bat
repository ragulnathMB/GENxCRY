@echo off
echo Setting up GENxCRY Virtual Environment
echo =====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo =====================================
echo Virtual environment setup complete!
echo =====================================
echo.
echo To run the application:
echo 1. Activate the environment: venv\Scripts\activate.bat
echo 2. Run the app: python main.py
echo.
echo Or simply run: run_venv.bat
echo.
pause
