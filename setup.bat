@echo off
REM eCourts Scraper - Windows Quick Setup Script

echo ==================================
echo 🎯 eCourts Intelligence Setup
echo ==================================
echo.

REM Check Python installation
echo ✓ Checking Python installation...
python --version
echo.

REM Create virtual environment
echo ✓ Creating virtual environment...
python -m venv venv
echo.

REM Activate virtual environment
echo ✓ Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Upgrade pip
echo ✓ Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install requirements
echo ✓ Installing dependencies...
pip install -r requirements.txt
echo.

REM Create necessary directories
echo ✓ Creating project directories...
if not exist "downloads" mkdir downloads
if not exist "results" mkdir results
if not exist "pdfs" mkdir pdfs
if not exist "logs" mkdir logs
if not exist "templates" mkdir templates
if not exist "static\css" mkdir static\css
if not exist "static\js" mkdir static\js
echo.

REM Check ChromeDriver
echo ✓ Checking ChromeDriver...
where chromedriver >nul 2>&1
if errorlevel 1 (
    echo   ⚠ ChromeDriver not found.
    echo   Please download from: https://chromedriver.chromium.org/
    echo   Extract and add to PATH or place in project folder
) else (
    echo   Found: ChromeDriver installed
)
echo.

echo ==================================
echo ✅ Setup Complete!
echo ==================================
echo.
echo To start the application:
echo 1. Run: venv\Scripts\activate
echo 2. Run: python app.py
echo 3. Open browser: http://localhost:5000
echo.
echo Happy scraping! 🚀
pauseversion >nul 2>&1
if errorlevel 1 (
    echo   ✗ Python not found. Please install Python 3.8+
    echo   Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --
