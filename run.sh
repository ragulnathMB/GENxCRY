#!/bin/bash

echo "Starting GENxCRY - AI Dataset Generator"
echo "By RN Software"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Install requirements if needed
echo "Installing/checking requirements..."
pip3 install -r requirements.txt

# Start the application
echo "Starting GENxCRY..."
python3 main.py
