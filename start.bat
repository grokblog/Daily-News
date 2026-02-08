@echo off
REM Quick Start Script for Grok Blog Generator
REM Windows version

echo ========================================
echo   Grok Blog Generator - Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo ⚠️  IMPORTANT: Please edit .env file and add your API keys!
    echo.
    pause
)

REM Menu
:menu
echo.
echo ========================================
echo   What would you like to do?
echo ========================================
echo.
echo 1. Generate blog content (test - 1 article)
echo 2. Generate blog content (5 articles)
echo 3. Build static site
echo 4. Generate and build
echo 5. Start local server
echo 6. Exit
echo.
set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" goto test
if "%choice%"=="2" goto generate
if "%choice%"=="3" goto build
if "%choice%"=="4" goto both
if "%choice%"=="5" goto serve
if "%choice%"=="6" goto end

echo Invalid choice. Please try again.
goto menu

:test
echo.
echo Generating test article...
python blog_generator.py --test
echo.
pause
goto menu

:generate
echo.
echo Generating 5 articles...
python blog_generator.py
echo.
pause
goto menu

:build
echo.
echo Building static site...
python build_site.py
echo.
pause
goto menu

:both
echo.
echo Generating content and building site...
python blog_generator.py
python build_site.py
echo.
pause
goto menu

:serve
echo.
echo Starting local server...
echo Open http://localhost:8000 in your browser
echo Press Ctrl+C to stop the server
echo.
cd public
python -m http.server 8000
cd ..
goto menu

:end
echo.
echo Thank you for using Grok Blog Generator!
echo.
pause
