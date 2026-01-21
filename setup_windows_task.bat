@echo off
REM ============================================================
REM Windows Task Scheduler Setup for Daily Job Search Pipeline
REM Run this script as Administrator
REM ============================================================

echo.
echo ========================================
echo Daily Job Search Pipeline - Task Setup
echo ========================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%daily_runner.py

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

echo Creating Windows Task Scheduler task...
echo.

REM Create the scheduled task
REM Runs daily at 9:00 AM
schtasks /create /tn "DailyJobSearch" /tr "python \"%PYTHON_SCRIPT%\" --run-once" /sc daily /st 09:00 /f

if errorlevel 1 (
    echo.
    echo ERROR: Failed to create scheduled task.
    echo Please run this script as Administrator.
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Task created successfully.
echo ========================================
echo.
echo Task Name: DailyJobSearch
echo Schedule: Daily at 9:00 AM
echo Script: %PYTHON_SCRIPT%
echo.
echo To view/modify the task:
echo   1. Open Task Scheduler (taskschd.msc)
echo   2. Look for "DailyJobSearch" in the task list
echo.
echo To run immediately:
echo   schtasks /run /tn "DailyJobSearch"
echo.
echo To delete the task:
echo   schtasks /delete /tn "DailyJobSearch" /f
echo.
pause
