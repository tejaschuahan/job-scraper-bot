# 🚀 24/7 Cloud Deployment Guide

Your job scraper bot is ready to deploy! Choose the option that works best for you.

---

## 📋 Prerequisites

Before deploying, you need:
- ✅ Your code (already done!)
- ✅ Telegram bot token (already in config.yaml)
- ✅ Git installed on your PC
- ✅ GitHub account (free)

---

## 🌟 Option 1: Railway (Recommended - Easiest)

**Free Tier**: $5 credit/month (enough for this bot)
**Deployment Time**: 5 minutes

### Step 1: Push to GitHub

```powershell
# Initialize git (if not already done)
cd E:\bot
git init
git add .
git commit -m "Initial commit - Job Scraper Bot"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/job-scraper-bot.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Railway

1. Go to https://railway.app
2. Sign up with GitHub (free)
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your `job-scraper-bot` repository
5. Railway will auto-detect Python and deploy!

### Step 3: Set Environment Variables (Optional)

If you want to hide your bot token:
1. In Railway dashboard → Variables tab
2. Add: `TELEGRAM_BOT_TOKEN` = your token
3. Update config.yaml to use environment variables

**Done!** Your bot is now running 24/7! 🎉

---

## 🐳 Option 2: Render (Free Forever Plan)

**Free Tier**: Unlimited (with small limitations)
**Deployment Time**: 5 minutes

### Step 1: Push to GitHub (same as above)

### Step 2: Deploy to Render

1. Go to https://render.com
2. Sign up with GitHub
3. Click "New" → "Background Worker"
4. Connect your GitHub repo
5. Configure:
   - **Name**: job-scraper-bot
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python interactive_bot.py`
6. Click "Create Background Worker"

**Done!** Bot running 24/7! 🎉

---

## ☁️ Option 3: AWS EC2 Free Tier (Most Control)

**Free Tier**: 750 hours/month for 12 months
**Deployment Time**: 15 minutes

### Step 1: Create EC2 Instance

1. Go to https://aws.amazon.com
2. Sign up for free tier
3. Launch EC2 instance:
   - **AMI**: Ubuntu 22.04 LTS
   - **Instance Type**: t2.micro (free tier)
   - **Key Pair**: Create new (download .pem file)
   - **Security Group**: Allow SSH (port 22)

### Step 2: Connect & Deploy

```bash
# Connect to your instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Install Python & dependencies
sudo apt update
sudo apt install python3-pip -y

# Clone your repository
git clone https://github.com/YOUR_USERNAME/job-scraper-bot.git
cd job-scraper-bot

# Install dependencies
pip3 install -r requirements.txt

# Run with systemd (stays running after logout)
sudo nano /etc/systemd/system/jobbot.service
```

Add this content:
```ini
[Unit]
Description=Job Scraper Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/job-scraper-bot
ExecStart=/usr/bin/python3 /home/ubuntu/job-scraper-bot/interactive_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable jobbot
sudo systemctl start jobbot
sudo systemctl status jobbot
```

**Done!** Bot running 24/7 with auto-restart! 🎉

---

## 🆓 Option 4: Google Cloud Run (Pay-as-you-go)

**Free Tier**: 2 million requests/month
**Deployment Time**: 10 minutes

### Step 1: Create Dockerfile

(Already created in your project!)

### Step 2: Deploy

```powershell
# Install Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/job-bot
gcloud run deploy job-bot --image gcr.io/YOUR_PROJECT_ID/job-bot --platform managed --region us-central1 --allow-unauthenticated
```

---

## 🎯 Quick Start: Railway (5 Minutes)

**I recommend Railway** because it's the easiest and has a generous free tier.

### Quick Steps:

1. **Create GitHub repo**:
   ```powershell
   cd E:\bot
   git init
   git add .
   git commit -m "Job Scraper Bot"
   ```

2. **Push to GitHub**:
   - Go to https://github.com/new
   - Create repo named `job-scraper-bot`
   - Follow the commands shown

3. **Deploy to Railway**:
   - Go to https://railway.app
   - Sign in with GitHub
   - "New Project" → "Deploy from GitHub"
   - Select `job-scraper-bot`
   - Wait 2 minutes... Done! ✅

4. **View Logs**:
   - Click on your deployment
   - Click "Logs" tab
   - See your bot running!

---

## 📊 Monitoring Your Bot

### Check if bot is running:
- Open Telegram
- Send `/status` to your bot
- Should respond immediately

### View logs:
- **Railway**: Dashboard → Logs tab
- **Render**: Dashboard → Logs tab
- **AWS**: `sudo journalctl -u jobbot -f`

### Restart bot:
- **Railway**: Dashboard → Restart button
- **Render**: Dashboard → Manual Deploy
- **AWS**: `sudo systemctl restart jobbot`

---

## 🔧 Troubleshooting

### Bot not responding?
1. Check logs for errors
2. Verify bot token is correct
3. Ensure config.yaml is uploaded
4. Check if service is running

### "Out of memory" errors?
- Upgrade to paid tier (Railway: $5/mo)
- Or use AWS t2.micro (free tier)

### Jobs not being sent?
- Check Telegram chat_id in config
- Verify sites are enabled in config.yaml
- Check logs for scraping errors

---

## 💰 Cost Comparison

| Platform | Free Tier | Paid (if needed) | Ease |
|----------|-----------|------------------|------|
| **Railway** | $5 credit/mo | $5/mo | ⭐⭐⭐⭐⭐ |
| **Render** | Forever free | $7/mo | ⭐⭐⭐⭐⭐ |
| **AWS EC2** | 12 months | $3.50/mo | ⭐⭐⭐ |
| **GCP** | $300 credit | Pay-as-go | ⭐⭐⭐ |

---

## 🎉 Next Steps

1. **Choose a platform** (I recommend Railway)
2. **Push code to GitHub**
3. **Deploy** (follow steps above)
4. **Test** by sending `/search` to your bot
5. **Enjoy** 24/7 job notifications!

---

## 📱 Using Your Bot

Once deployed, anyone can use your bot:
1. Search for your bot in Telegram: `@YourBotName`
2. Send `/start` to begin
3. Send `/search` to find jobs
4. Bot runs continuously for each user!

**Multiple users can use the bot simultaneously!**

---

## 🔐 Security Tips

1. **Never commit secrets** to GitHub:
   ```bash
   # Add to .gitignore
   echo "config.yaml" >> .gitignore
   echo "*.db" >> .gitignore
   echo "*.log" >> .gitignore
   ```

2. **Use environment variables**:
   - Store bot token as env var
   - Store chat_id as env var

3. **Make repo private** on GitHub (free with GitHub account)

---

## 📞 Support

If you need help:
1. Check the logs first
2. Review this guide
3. Test locally before deploying
4. Ensure all dependencies are in requirements.txt

**Your bot is ready to deploy!** Choose a platform and follow the steps above. Railway is the quickest! 🚀
