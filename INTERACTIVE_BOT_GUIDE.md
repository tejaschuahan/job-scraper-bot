# 🤖 Interactive Job Scraper Bot - User Guide

## 📱 How to Use

The bot is now running and waiting for your commands in Telegram!

### 🚀 Getting Started

1. **Open Telegram** and find your bot
2. **Start conversation**: Send `/start`
3. **Begin search**: Send `/search`

### 📋 Available Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and introduction |
| `/search` | Start a new job search |
| `/stop` | Stop your current active search |
| `/status` | Check your current search status |
| `/help` | Show help and instructions |

### 🎯 How Job Search Works

1. **Send `/search`** command
2. **Choose a role** from the keyboard:
   - Data Analyst
   - Data Scientist
   - Data Engineer
   - Business Analyst
   - Financial Analyst
   - Product Analyst
   - Marketing Analyst
   - Operations Analyst
   - Power BI Developer
   - Tableau Developer
   - Or type your own custom role!

3. **Bot automatically finds related roles**:
   - If you select "Data Analyst", it will also search for:
     - Business Analyst
     - Business Intelligence Analyst
     - BI Analyst
     - Insights Analyst
     - Reporting Analyst
     - Analytics Engineer

4. **Confirm to start**: Type `YES` to begin scraping

5. **Receive jobs**: You'll get notifications for new jobs every 5 minutes!

### 💡 Example Conversation

```
You: /search
Bot: 🎯 What job role are you looking for?
     [Shows keyboard with options]

You: Data Analyst
Bot: ✅ Got it! I'll search for Data Analyst
     📋 I'll also include these related roles:
       • Data Analyst
       • Business Analyst
       • Business Intelligence Analyst
       • BI Analyst
       • Insights Analyst
       • Reporting Analyst
       • Analytics Engineer
     
     Ready to start? Type 'YES' to begin.

You: YES
Bot: 🚀 Starting job search for Data Analyst!
     🔄 Running first scrape now...
     
     [After scraping completes]
     
     📬 New Job Found!
     
     🏢 Data Analyst at Accenture
     📍 Bangalore, India
     💰 Not specified
     🔗 https://linkedin.com/jobs/...
```

### 🛑 Stopping a Search

Send `/stop` at any time to stop your active job search.

### 📊 Checking Status

Send `/status` to see:
- What role you're searching for
- All related roles being searched
- How long the bot has been running

### 🌐 What Sites Are Scraped?

The bot searches across:
- ✅ **LinkedIn** - 400+ jobs per cycle
- ✅ **TimesJobs** - 400+ jobs per cycle
- ✅ **Remotive** - Remote tech jobs
- ✅ **LinkedIn Posts** - Job posts in feed
- ⚠️ **Naukri** - India's largest job site
- ⚠️ **Foundit** (Monster India)
- ⚠️ **Shine** - Tech jobs India
- ⚠️ **Freshersworld** - Entry-level jobs
- ❌ **Instahyre** - Blocked (403)
- ❌ **Cutshort** - Incorrect URLs
- ❌ **Hirist** - Incorrect URLs
- ❌ **IIMJobs** - Incorrect URLs

**Total: 800+ jobs per scraping cycle!**

### ⏰ How Often Does It Scrape?

- **Initial scrape**: Immediately after you confirm
- **Recurring scrapes**: Every **5 minutes**
- **Status updates**: Every 10 cycles (~50 minutes)

### 🎛️ Customization

Want to change settings? Edit `config.yaml`:

```yaml
# Change scraping interval
scraping:
  interval: 300  # 5 minutes (change to any number of seconds)

# Change location
search:
  default_location: "India"  # Change to any location

# Change filters
filters:
  exclude_keywords:
    - "senior"    # Remove to include senior roles
    - "lead"      # Remove to include lead roles
    - "manager"   # Remove to include manager roles
```

### 🔥 Tips for Best Results

1. **Be specific**: Instead of just "analyst", try "data analyst" or "financial analyst"
2. **Use keywords**: The bot searches for related roles automatically
3. **Check frequently**: New jobs are posted throughout the day
4. **Multiple searches**: You can stop and start different searches anytime
5. **Adjust filters**: If you're getting too many/few results, edit `config.yaml`

### 🐛 Troubleshooting

**Not receiving jobs?**
- Check `/status` to see if search is active
- Make sure the bot has sent you the initial "Starting job search" message
- Wait 5 minutes for the first cycle to complete

**Too many jobs?**
- Add more exclude keywords in `config.yaml`
- Be more specific with your job role

**Too few jobs?**
- Remove exclude keywords (senior, lead, manager)
- Try broader role names (e.g., "analyst" instead of "business intelligence analyst")

**Bot not responding?**
- Check if `interactive_bot.py` is still running
- Restart with: `python interactive_bot.py`
- Or double-click: `START_INTERACTIVE_BOT.bat`

### 📝 Technical Details

**Database**: Jobs are stored in `jobs.db` SQLite database
- Tracks all seen jobs with MD5 hashing
- Prevents duplicate notifications
- Keeps 30 days of history

**Deduplication**: Uses MD5 hash of:
- Job title (normalized)
- Company name (normalized)
- Job URL

**Filtering**: Jobs must:
- Match at least one include keyword
- Not match any exclude keyword
- Match location (if specified)

### 🚀 Running 24/7

**On Windows:**
```batch
START_INTERACTIVE_BOT.bat
```

**On Linux/Mac:**
```bash
source .venv/bin/activate
python interactive_bot.py &
```

**Using Screen (keeps running after logout):**
```bash
screen -S jobbot
source .venv/bin/activate
python interactive_bot.py
# Press Ctrl+A then D to detach
# To reattach: screen -r jobbot
```

**Using systemd (Linux):**
Create `/etc/systemd/system/jobbot.service`:
```ini
[Unit]
Description=Interactive Job Scraper Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/bot
ExecStart=/path/to/bot/.venv/bin/python /path/to/bot/interactive_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable jobbot
sudo systemctl start jobbot
sudo systemctl status jobbot
```

### 📞 Support

If you need help:
1. Check this guide
2. Review `config.yaml` settings
3. Check the terminal output for errors
4. Verify your Telegram bot token is correct

### 🎉 Enjoy!

Your personal job search assistant is now ready! Just send `/search` in Telegram and let the bot do the work! 🚀
