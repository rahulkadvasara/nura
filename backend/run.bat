@echo off
REM Nura Backend - Windows Batch Script
REM Simple script to start the backend server on Windows

echo 🏥 Nura Backend - Development Server
echo ====================================

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo ✅ Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  Virtual environment not found, using system Python
)

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found
    echo 💡 Copy .env.example to .env and configure your settings
    pause
    exit /b 1
)

REM Start the server
echo 🚀 Starting server...
python run.py

pause