@echo off
echo ============================================================
echo LINKEDIN RESEARCH + AUTOMATION WORKFLOW
echo ============================================================
echo.
echo This batch file runs the complete workflow:
echo 1. Research companies for HR + VIT alumni leads
echo 2. Transfer leads to contacts
echo 3. Run automation to send connection requests + messages
echo.

cd /d D:\gitcode\Projects\Linkedin_Automation
call .venv\Scripts\activate.bat

:menu
echo.
echo ============================================================
echo MENU
echo ============================================================
echo 1. Research next company
echo 2. Transfer leads to contacts
echo 3. Run automation (send requests + messages)
echo 4. Show research progress
echo 5. Research ALL companies (slow - 1 per 10 min)
echo 6. Exit
echo.
set /p choice=Enter choice (1-6): 

if "%choice%"=="1" goto research
if "%choice%"=="2" goto transfer
if "%choice%"=="3" goto automate
if "%choice%"=="4" goto progress
if "%choice%"=="5" goto research_all
if "%choice%"=="6" goto end
goto menu

:research
echo.
echo Researching next company...
python linkedin_researcher.py next
goto menu

:transfer
echo.
echo Transferring leads to contacts...
python linkedin_researcher.py transfer
goto menu

:automate
echo.
echo Starting automation...
python main.py
goto menu

:progress
echo.
python temp_reset.py
goto menu

:research_all
echo.
echo This will research all companies with 10 min delay between each.
echo Press Ctrl+C to stop at any time.
echo.
python -c "from linkedin_researcher import LinkedInResearcher; r = LinkedInResearcher(); r.load_companies(); import time; [r.research_company(c) or time.sleep(600) for c in ['SuperAGI', 'Postman', 'Icertis', 'HighRadius', 'Tiger Analytics', 'Tredence', 'Zipy.ai', 'Soroco']]"
goto menu

:end
echo Goodbye!
pause
