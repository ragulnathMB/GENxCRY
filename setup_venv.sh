#!/bin/bash

echo "Setting up GENxCRY Virtual Environment"
echo "====================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "====================================="
echo "Virtual environment setup complete!"
echo "====================================="
echo ""
echo "To run the application:"
echo "1. Activate the environment: source venv/bin/activate"
echo "2. Run the app: python main.py"
echo ""
echo "Or simply run: ./run_venv.sh"
echo ""
