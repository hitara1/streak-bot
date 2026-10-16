@echo off
chcp 65001 >nul
echo 🔥 Habit Streak Bot - Windows Setup
echo =================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python from python.org
    echo    Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Install dependencies
echo 📦 Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed!
echo.

REM Check .env file
if not exist .env (
    echo ⚠️  .env file not found!
    echo    Creating from template...
    copy .env.example .env
    echo    ✅ Created .env — PLEASE EDIT IT and add your BOT_TOKEN!
    echo.
    echo    Get your token from @BotFather on Telegram
    echo    Then open .env and replace: BOT_TOKEN=your_token_here
) else (
    echo ✅ .env file found
)

echo.
echo =================================
echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit .env and add your BOT_TOKEN
echo 2. Run: python run.py
echo.
pause
