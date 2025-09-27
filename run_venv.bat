@echo off
echo Starting GENxCRY in Virtual Environment
echo =======================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found!
    echo Please run setup_venv.bat first to create the environment.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
python -c "import cv2, PIL, numpy, tkinter" >nul 2>&1
if errorlevel 1 (
    echo Some dependencies are missing. Installing...
    pip install -r requirements.txt
)

REM Start the application
echo.
echo Starting GENxCRY - AI Dataset Generator...
echo ==========================================
python main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
