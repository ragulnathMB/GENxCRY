#!/bin/bash

echo "Starting GENxCRY in Virtual Environment"
echo "======================================="
echo ""

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "Virtual environment not found!"
    echo "Please run ./setup_venv.sh first to create the environment."
    echo ""
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
python -c "import cv2, PIL, numpy, tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Some dependencies are missing. Installing..."
    pip install -r requirements.txt
fi

# Start the application
echo ""
echo "Starting GENxCRY - AI Dataset Generator..."
echo "=========================================="
python main.py
