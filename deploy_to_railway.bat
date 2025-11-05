@echo off
echo ================================================
echo    RAILWAY DEPLOYMENT SCRIPT
echo ================================================
echo.

echo Step 1: Checking git...
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed!
    echo Please install Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo [OK] Git is installed

echo.
echo Step 2: Initialize git repository...
if not exist .git (
    git init
    echo [OK] Git repository initialized
) else (
    echo [OK] Git repository already exists
)

echo.
echo Step 3: Add files to git...
git add .
git commit -m "Prepare for deployment"
echo [OK] Files committed

echo.
echo ================================================
echo    NEXT STEPS:
echo ================================================
echo.
echo 1. Create a GitHub repository:
echo    - Go to: https://github.com/new
echo    - Repository name: job-scraper-bot
echo    - Make it Private (recommended)
echo    - Click "Create repository"
echo.
echo 2. Push your code:
echo    git remote add origin https://github.com/YOUR_USERNAME/job-scraper-bot.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 3. Deploy to Railway:
echo    - Go to: https://railway.app
echo    - Sign in with GitHub
echo    - Click "New Project"
echo    - Select "Deploy from GitHub repo"
echo    - Choose "job-scraper-bot"
echo    - Wait 2 minutes... Done!
echo.
echo ================================================

pause
