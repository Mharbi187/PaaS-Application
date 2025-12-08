@echo off
REM PaaS Application Startup Script
REM Automatically handles common startup issues

echo ====================================
echo    PaaS Application Launcher
echo ====================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Creating .env from .env.example...
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo [SUCCESS] .env file created. Please configure it before running again.
    ) else (
        echo [ERROR] .env.example not found!
    )
    pause
    exit /b 1
)

REM Stop any existing Python processes (optional)
echo Checking for existing Flask instances...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

REM Create necessary directories
if not exist "logs" mkdir logs
if not exist "ssh_keys" mkdir ssh_keys
if not exist "terraform\states" mkdir "terraform\states"
if not exist "instance" mkdir instance

REM Start the application
echo.
echo Starting PaaS Application...
echo.
".venv\Scripts\python.exe" app.py

REM If app exits with error
if errorlevel 1 (
    echo.
    echo [ERROR] Application failed to start!
    echo Check logs\paas.log for details
    pause
)
