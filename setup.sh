#!/bin/bash

# eCourts Scraper - Quick Setup Script
# This script automates the entire setup process

echo "=================================="
echo "🎯 eCourts Intelligence Setup"
echo "=================================="
echo ""

# Check Python installation
echo "✓ Checking Python installation..."
if command -v python3 &> /dev/null
then
    PYTHON_VERSION=$(python3 --version)
    echo "  Found: $PYTHON_VERSION"
else
    echo "  ✗ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Create virtual environment
echo ""
echo "✓ Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "✓ Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Mac/Linux
    source venv/bin/activate
fi

# Upgrade pip
echo ""
echo "✓ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "✓ Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo ""
echo "✓ Creating project directories..."
mkdir -p downloads
mkdir -p results
mkdir -p pdfs
mkdir -p logs
mkdir -p templates
mkdir -p static/css
mkdir -p static/js

# Check ChromeDriver
echo ""
echo "✓ Checking ChromeDriver..."
if command -v chromedriver &> /dev/null
then
    echo "  Found: ChromeDriver installed"
else
    echo "  ⚠ ChromeDriver not found. Please install it:"
    echo "    Windows: Download from https://chromedriver.chromium.org/"
    echo "    Mac: brew install --cask chromedriver"
    echo "    Linux: sudo apt-get install chromium-chromedriver"
fi

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "To start the application:"
echo "1. Activate virtual environment:"
echo "   - Windows: venv\\Scripts\\activate"
echo "   - Mac/Linux: source venv/bin/activate"
echo "2. Run: python app.py"
echo "3. Open: http://localhost:5000"
echo ""
echo "Happy scraping! 🚀"
