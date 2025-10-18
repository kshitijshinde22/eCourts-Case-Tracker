@echo off
REM eCourts Scraper - Windows Quick Setup Script

echo ==================================
echo 🎯 eCourts Intelligence Setup
echo ==================================
echo.

REM Check Python installation
echo ✓ Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ✗ Python not found. Please install Python 3.8+
    echo   Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --
