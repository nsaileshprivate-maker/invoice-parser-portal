@echo off
REM Invoice & Shipment Bill Parser Portal - Quick Start Script (Windows)
REM Run this script to set up and start the application

cls
echo =========================================
echo Invoice ^& Shipment Bill Parser Portal
echo Quick Start Setup
echo =========================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)
for /f "tokens=*" %%A in ('python --version 2^>^&1') do set python_version=%%A
echo   Found: %python_version%

REM Check pip
echo.
echo Checking pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: pip is not installed
    pause
    exit /b 1
)
echo   pip is available

REM Install dependencies
echo.
echo Installing Python dependencies...
echo   This may take a few minutes...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error installing dependencies
    pause
    exit /b 1
)
echo   Dependencies installed successfully

REM Create uploads directory
echo.
echo Creating uploads directory...
if not exist uploads mkdir uploads

REM Initialize database
echo.
echo Initializing database...
python -c "from app import init_db; init_db(); print('   Database initialized')"

REM Run the application
echo.
echo =========================================
echo Setup complete!
echo.
echo Starting Flask server...
echo =========================================
echo.
echo Open your browser and go to:
echo    http://localhost:5000
echo.
echo To stop the server, press Ctrl+C
echo =========================================
echo.

python app.py
pause
