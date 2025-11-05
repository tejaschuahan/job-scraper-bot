@echo off
title Interactive Job Scraper Bot
echo ============================================================
echo     INTERACTIVE JOB SCRAPER BOT
echo ============================================================
echo.
echo Starting the interactive Telegram bot...
echo.
echo The bot will:
echo   - Ask users for their desired job role
echo   - Automatically find related positions
echo   - Scrape jobs every 5 minutes
echo   - Send new jobs directly to Telegram
echo.
echo Commands in Telegram:
echo   /start   - Welcome message
echo   /search  - Start job search
echo   /stop    - Stop your search
echo   /status  - Check search status
echo.
echo Press Ctrl+C to stop the bot
echo ============================================================
echo.

cd /d "%~dp0"
call .venv\Scripts\activate.bat
python interactive_bot.py

pause
