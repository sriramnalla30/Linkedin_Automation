@echo off
REM ============================================
REM LinkedIn Automation - Windows Task Scheduler Setup
REM This creates a scheduled task to run automatically
REM ============================================

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║   LinkedIn Automation - Task Scheduler Setup               ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

set PYTHON_PATH=D:\gitcode\Projects\Linkedin_Automation\.venv\Scripts\python.exe
set SCRIPT_PATH=D:\gitcode\Projects\Linkedin_Automation\auto_scheduler.py
set TASK_NAME=LinkedInAutoChecker

echo This will create a Windows Task to:
echo   - Run every 1 hour when you're logged in
echo   - Check for accepted LinkedIn connections
echo   - Auto-send messages to new connections
echo.

echo [1] Create scheduled task (runs every hour)
echo [2] Create scheduled task (runs every 30 minutes)
echo [3] Remove scheduled task
echo [4] Run once now (test)
echo [5] Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto create_hourly
if "%choice%"=="2" goto create_30min
if "%choice%"=="3" goto remove_task
if "%choice%"=="4" goto run_once
if "%choice%"=="5" goto end

:create_hourly
echo.
echo Creating hourly task...
schtasks /create /tn "%TASK_NAME%" /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\" --once" /sc hourly /mo 1 /f
if %errorlevel%==0 (
    echo ✅ Task created successfully!
    echo    Task will run every hour when you're logged in.
) else (
    echo ❌ Failed to create task. Try running as Administrator.
)
goto end

:create_30min
echo.
echo Creating 30-minute task...
schtasks /create /tn "%TASK_NAME%" /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\" --once" /sc minute /mo 30 /f
if %errorlevel%==0 (
    echo ✅ Task created successfully!
    echo    Task will run every 30 minutes when you're logged in.
) else (
    echo ❌ Failed to create task. Try running as Administrator.
)
goto end

:remove_task
echo.
echo Removing task...
schtasks /delete /tn "%TASK_NAME%" /f
if %errorlevel%==0 (
    echo ✅ Task removed successfully!
) else (
    echo ❌ Task not found or failed to remove.
)
goto end

:run_once
echo.
echo Running once now...
"%PYTHON_PATH%" "%SCRIPT_PATH%" --once
goto end

:end
echo.
pause
