# Job Scraper Bot - Deployment Setup Script
# Run this in PowerShell

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   JOB SCRAPER BOT - DEPLOYMENT SETUP" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Add Git to PATH for this session
$env:Path += ";C:\Program Files\Git\cmd;C:\Program Files\Git\bin"

Write-Host "Step 1: Checking Git..." -ForegroundColor Yellow
try {
    $gitVersion = git --version
    Write-Host "[OK] $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Git not found!" -ForegroundColor Red
    Write-Host "Please restart PowerShell after installing Git" -ForegroundColor Red
    Write-Host "Or run: `$env:Path += ';C:\Program Files\Git\cmd'" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host ""

Write-Host "Step 2: Configure Git (first time)..." -ForegroundColor Yellow
git config --global user.name "tejaschauan"
git config --global user.email "tejas@example.com"
Write-Host "[OK] Git configured" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Initialize Git repository..." -ForegroundColor Yellow
if (-not (Test-Path .git)) {
    git init
    Write-Host "[OK] Repository initialized" -ForegroundColor Green
} else {
    Write-Host "[OK] Repository already exists" -ForegroundColor Green
}
Write-Host ""

Write-Host "Step 4: Add all files..." -ForegroundColor Yellow
git add .
Write-Host "[OK] Files added" -ForegroundColor Green
Write-Host ""

Write-Host "Step 5: Create commit..." -ForegroundColor Yellow
git commit -m "Initial commit - Job Scraper Bot"
Write-Host "[OK] Committed" -ForegroundColor Green
Write-Host ""

Write-Host "Step 6: Rename branch to main..." -ForegroundColor Yellow
git branch -M main
Write-Host "[OK] Branch renamed" -ForegroundColor Green
Write-Host ""

Write-Host "Step 7: Add remote repository..." -ForegroundColor Yellow
try {
    git remote add origin https://github.com/tejaschauan/job-scraper-bot.git
    Write-Host "[OK] Remote added" -ForegroundColor Green
} catch {
    Write-Host "[INFO] Remote may already exist" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   READY TO PUSH!" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Now run this command to push to GitHub:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "If it asks for credentials:" -ForegroundColor Yellow
Write-Host "- Username: tejaschauan" -ForegroundColor White
Write-Host "- Password: Use Personal Access Token" -ForegroundColor White
Write-Host "  Get token: https://github.com/settings/tokens" -ForegroundColor Cyan
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   AFTER PUSHING:" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Deploy to Railway:" -ForegroundColor Yellow
Write-Host "1. Go to https://railway.app" -ForegroundColor White
Write-Host "2. Sign in with GitHub" -ForegroundColor White
Write-Host "3. New Project -> Deploy from GitHub" -ForegroundColor White
Write-Host "4. Select 'job-scraper-bot'" -ForegroundColor White
Write-Host "5. Done in 2 minutes!" -ForegroundColor Green
Write-Host ""

pause
