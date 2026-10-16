@echo off
chcp 65001 >nul
echo 🔥 Starting Habit Streak Bot...
python run.py
if errorlevel 1 (
    echo.
    echo ❌ Bot crashed. Check the error above.
    pause
)
