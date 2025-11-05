@echo off
echo ================================================
echo    JOB SCRAPER BOT - DEPLOYMENT SETUP
echo ================================================
echo.

REM Set Git path (adjust if Git is installed elsewhere)
set "PATH=%PATH%;C:\Program Files\Git\cmd;C:\Program Files\Git\bin"

echo Step 1: Checking Git installation...
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git not found in PATH!
    echo.
    echo Please close this window and open a NEW PowerShell/Command Prompt
    echo After installing Git, you need to restart your terminal.
    echo.
    pause
    exit /b 1
)

git --version
echo [OK] Git is working!
echo.

echo Step 2: Configure Git (first time setup)...
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
echo [INFO] You can change these later with:
echo        git config --global user.name "Your Real Name"
echo        git config --global user.email "youremail@example.com"
echo.

echo Step 3: Initialize Git repository...
if not exist .git (
    git init
    echo [OK] Git repository initialized
) else (
    echo [OK] Git repository already exists
)
echo.

echo Step 4: Add all files to Git...
git add .
echo [OK] Files added
echo.

echo Step 5: Create initial commit...
git commit -m "Initial commit - Job Scraper Bot ready for deployment"
if %errorlevel% neq 0 (
    echo [WARNING] Commit may have failed or nothing to commit
)
echo.

echo Step 6: Rename branch to main...
git branch -M main
echo [OK] Branch renamed to main
echo.

echo ================================================
echo    NEXT STEPS - COPY AND PASTE THESE COMMANDS:
echo ================================================
echo.
echo 1. Add your GitHub repository:
echo.
echo    git remote add origin https://github.com/tejaschauan/job-scraper-bot.git
echo.
echo 2. Push to GitHub:
echo.
echo    git push -u origin main
echo.
echo 3. If it asks for credentials:
echo    - Username: your GitHub username
echo    - Password: use a Personal Access Token (not your password)
echo      Get token at: https://github.com/settings/tokens
echo.
echo ================================================
echo    AFTER PUSHING TO GITHUB:
echo ================================================
echo.
echo Deploy to Railway:
echo 1. Go to: https://railway.app
echo 2. Sign in with GitHub
echo 3. Click "New Project"
echo 4. Select "Deploy from GitHub repo"
echo 5. Choose "job-scraper-bot"
echo 6. Wait 2 minutes... DONE!
echo.
echo ================================================

pause
