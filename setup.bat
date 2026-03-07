@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title YouTube Automation - Setup

echo.
echo ========================================
echo   YouTube Automation - Setup Script
echo ========================================
echo.

REM =============================================
REM 1. Check Python installation
REM =============================================
echo [1/6] Checking Python installation...

where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH.
    echo.
    echo Please install Python from https://python.org
    echo IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

REM Check Python version (need 3.10+)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo   Found Python %PYVER%

REM =============================================
REM 2. Check FFmpeg installation
REM =============================================
echo [2/6] Checking FFmpeg installation...

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: FFmpeg is not installed or not in PATH.
    echo.
    echo FFmpeg is REQUIRED for video processing.
    echo.
    echo How to install FFmpeg:
    echo   1. Download from https://ffmpeg.org/download.html
    echo   2. Extract to C:\ffmpeg
    echo   3. Add C:\ffmpeg\bin to your system PATH
    echo   4. Restart this terminal and run setup.bat again
    echo.
    echo OR install via winget:
    echo   winget install Gyan.FFmpeg
    echo.
    set /p CONTINUE="Continue without FFmpeg? (y/n): "
    if /i not "!CONTINUE!"=="y" (
        pause
        exit /b 1
    )
) else (
    echo   FFmpeg found!
)

REM =============================================
REM 3. Create virtual environment
REM =============================================
echo [3/6] Setting up virtual environment...

if exist venv (
    echo   Removing old virtual environment...
    rmdir /s /q venv 2>nul
    timeout /t 2 /nobreak >nul
)

echo   Creating new virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    echo Try: python -m ensurepip --upgrade
    pause
    exit /b 1
)

REM =============================================
REM 4. Activate and upgrade pip
REM =============================================
echo [4/6] Activating environment and upgrading pip...

call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet

REM =============================================
REM 5. Install dependencies
REM =============================================
echo [5/6] Installing dependencies (this may take 2-3 minutes)...

pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo WARNING: Some packages may have failed to install.
    echo Trying to install core packages individually...
    echo.
    pip install openai requests python-dotenv schedule edge-tts
    pip install moviepy pillow
    pip install google-auth google-auth-oauthlib google-api-python-client
    pip install chromadb sentence-transformers 2>nul
    echo.
    echo Core packages installed. ChromaDB may have failed on Python 3.14+ (this is OK - JSON fallback will be used).
)

REM =============================================
REM 6. Create .env if it doesn't exist
REM =============================================
echo [6/6] Checking configuration...

if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo.
        echo IMPORTANT: .env file created from template.
        echo You MUST edit .env and add your API keys:
        echo   - GROQ_API_KEY   (free from https://console.groq.com/keys)
        echo   - PEXELS_API_KEY (free from https://www.pexels.com/api/)
        echo.
    ) else (
        echo # API Keys - Replace with your actual secret keys> .env
        echo.>> .env
        echo # Get your FREE Groq API key from: https://console.groq.com/keys>> .env
        echo GROQ_API_KEY=your-groq-api-key-here>> .env
        echo.>> .env
        echo # Get your Pexels API key from: https://www.pexels.com/api/>> .env
        echo PEXELS_API_KEY=your-pexels-api-key-here>> .env
        echo.>> .env
        echo # Path to YouTube credentials file>> .env
        echo YOUTUBE_CREDENTIALS_PATH=./youtube_credentials.json>> .env
        echo.
        echo IMPORTANT: .env file created. You MUST edit it with your API keys!
        echo.
    )
) else (
    echo   .env file already exists.
)

REM Create output and logs directories
if not exist output mkdir output
if not exist logs mkdir logs
if not exist rag_data mkdir rag_data

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit .env file with your API keys (if not done already)
echo   2. Add youtube_credentials.json (Google OAuth2 file)
echo   3. Run the project:
echo.
echo      venv\Scripts\activate
echo      python main.py
echo.
echo   Or with a specific topic:
echo      python main.py --topic "5 facts about the ocean"
echo.
echo ========================================
pause
