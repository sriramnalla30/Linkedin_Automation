@echo off
REM ============================================
REM LinkedIn Automation - Background Runner
REM ============================================
REM Double-click this file to start automation
REM It will check for accepted connections every 30 minutes
REM and send messages automatically!
REM ============================================

echo ============================================
echo    LINKEDIN AUTOMATION - BACKGROUND MODE
echo ============================================
echo.
echo This will run in background and:
echo  - Check for accepted connections every 30 mins
echo  - Send personalized messages automatically
echo  - Log all activity to automation_log.txt
echo.
echo DO NOT CLOSE THIS WINDOW!
echo (You can minimize it)
echo.
echo ============================================

cd /d D:\gitcode\Projects\Linkedin_Automation

REM Activate virtual environment and run
D:\gitcode\Projects\Linkedin_Automation\.venv\Scripts\python.exe auto_scheduler.py

REM If script exits, pause to see any errors
echo.
echo Script stopped. Press any key to close...
pause > nul
