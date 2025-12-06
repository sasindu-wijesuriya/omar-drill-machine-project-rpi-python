@echo off
REM Start the GPIO Simulator
echo ============================================================
echo Starting Raspberry Pi GPIO Simulator
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

REM Start the simulator
echo Starting simulator on http://localhost:8100
echo Press Ctrl+C to stop
echo.
python simulator.py

pause
