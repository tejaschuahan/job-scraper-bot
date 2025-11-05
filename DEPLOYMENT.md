# Job Scraper Bot - Complete Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Telegram Bot Token (get from @BotFather)
- Telegram Chat ID (get from @userinfobot)

### Installation

1. **Clone or download the bot files:**
```bash
cd /path/to/bot
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure the bot:**
   - Edit `config.yaml` with your settings
   - Add your Telegram bot token and chat ID
   - Customize search queries and filters

4. **Run the bot:**
```bash
python job_scraper.py
```

---

## 🔧 Configuration Guide

### Getting Your Telegram Credentials

1. **Bot Token:**
   - Open Telegram and search for @BotFather
   - Send `/newbot` and follow the instructions
   - Copy the token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Chat ID:**
   - Search for @userinfobot on Telegram
   - Send `/start` to get your chat ID
   - Or use @RawDataBot and forward a message

### Editing config.yaml

```yaml
telegram:
  bot_token: "YOUR_TOKEN_HERE"
  chat_id: "YOUR_CHAT_ID_HERE"

search:
  queries:
    - "data analyst"        # Add your job titles
    - "python developer"
  default_location: "Remote"  # Or specific city

sites:
  linkedin:
    enabled: true
  glassdoor:
    enabled: true
  google_jobs:
    enabled: true
  indeed:
    enabled: true

scraping:
  interval: 300              # 5 minutes = 300 seconds

filters:
  include_keywords:
    - "python"
    - "sql"
  exclude_keywords:
    - "senior"
    - "manager"
  remote_only: false
```

---

## 🐧 Linux VPS Deployment (24/7 with systemd)

### Method 1: systemd Service

1. **Prepare the environment:**
```bash
# Create project directory
mkdir -p ~/job-scraper
cd ~/job-scraper

# Copy files
# Upload job_scraper.py, config.yaml, requirements.txt

# Install dependencies
python3 -m pip install --user -r requirements.txt
```

2. **Create log directory:**
```bash
sudo mkdir -p /var/log/job-scraper
sudo chown $USER:$USER /var/log/job-scraper
```

3. **Install the service:**
```bash
# Edit the service file first
nano job-scraper.service

# Replace YOUR_USERNAME with your actual username
# Update paths if different

# Copy to systemd
sudo cp job-scraper.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable job-scraper

# Start service
sudo systemctl start job-scraper
```

4. **Manage the service:**
```bash
# Check status
sudo systemctl status job-scraper

# View logs
sudo journalctl -u job-scraper -f

# Restart
sudo systemctl restart job-scraper

# Stop
sudo systemctl stop job-scraper

# Disable auto-start
sudo systemctl disable job-scraper
```

### Method 2: Using screen/tmux (Quick & Simple)

```bash
# Using screen
screen -S job-scraper
python3 job_scraper.py
# Press Ctrl+A then D to detach

# To reattach
screen -r job-scraper

# Or using tmux
tmux new -s job-scraper
python3 job_scraper.py
# Press Ctrl+B then D to detach

# To reattach
tmux attach -t job-scraper
```

---

## 🐳 Docker Deployment

### Option 1: Docker Compose (Recommended)

1. **Prepare files:**
```bash
# Ensure you have:
# - Dockerfile
# - docker-compose.yml
# - config.yaml (configured)
# - requirements.txt
# - job_scraper.py

# Create data and logs directories
mkdir -p data logs
```

2. **Configure:**
Edit `config.yaml` with your credentials and settings.

3. **Build and run:**
```bash
# Build image
docker-compose build

# Start container in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down

# Restart container
docker-compose restart
```

4. **Manage the container:**
```bash
# View status
docker-compose ps

# Stop
docker-compose stop

# Start
docker-compose start

# Remove everything
docker-compose down -v
```

### Option 2: Plain Docker

```bash
# Build image
docker build -t job-scraper .

# Run container
docker run -d \
  --name job-scraper-bot \
  --restart unless-stopped \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  job-scraper

# View logs
docker logs -f job-scraper-bot

# Stop container
docker stop job-scraper-bot

# Remove container
docker rm job-scraper-bot
```

---

## ☁️ Cloud Deployment

### AWS EC2

1. **Launch EC2 instance:**
   - Ubuntu 22.04 LTS
   - t2.micro (free tier eligible)
   - Configure security group (no inbound rules needed)

2. **Connect and setup:**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip -y

# Install Docker (optional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Clone/upload your bot files
git clone your-repo-url
cd job-scraper

# Follow Linux VPS or Docker deployment steps above
```

### DigitalOcean Droplet

1. **Create Droplet:**
   - Ubuntu 22.04
   - Basic plan ($4-6/month)

2. **Setup:**
```bash
ssh root@your-droplet-ip

# Create user
adduser jobscraper
usermod -aG sudo jobscraper
su - jobscraper

# Follow Linux VPS deployment steps
```

### Google Cloud Platform

1. **Create Compute Engine instance:**
   - e2-micro (free tier)
   - Ubuntu 22.04 LTS

2. **Setup identical to AWS EC2**

### Heroku (Not Recommended)

Heroku's free tier restarts daily and doesn't persist files well. Better to use VPS or cloud VM.

---

## 📊 Monitoring & Maintenance

### Check if Bot is Running

```bash
# For systemd
sudo systemctl status job-scraper

# For Docker
docker ps | grep job-scraper

# For screen/tmux
screen -ls
```

### View Logs

```bash
# Application logs
tail -f job_scraper.log

# Systemd logs
sudo journalctl -u job-scraper -f

# Docker logs
docker logs -f job-scraper-bot
```

### Database Queries

```bash
# Open database
sqlite3 jobs.db

# Count total jobs
SELECT COUNT(*) FROM jobs;

# Recent jobs
SELECT title, company, site, scraped_at 
FROM jobs 
ORDER BY scraped_at DESC 
LIMIT 10;

# Jobs per site
SELECT site, COUNT(*) as count 
FROM jobs 
GROUP BY site;

# Exit
.exit
```

### Backup Database

```bash
# Create backup
cp jobs.db jobs_backup_$(date +%Y%m%d).db

# Or with Docker
docker cp job-scraper-bot:/app/data/jobs.db ./backup/jobs.db
```

---

## 🔍 Troubleshooting

### Bot Not Starting

1. Check configuration:
```bash
python3 -c "import yaml; print(yaml.safe_load(open('config.yaml')))"
```

2. Check dependencies:
```bash
pip install -r requirements.txt --upgrade
```

3. Check Telegram credentials:
   - Verify bot token is correct
   - Ensure chat_id is correct
   - Test manually: send a message to your bot

### No Jobs Found

1. Check if sites are enabled in `config.yaml`
2. Verify search queries are relevant
3. Check if filters are too restrictive
4. Review logs for errors

### Rate Limiting / Blocked

1. Increase delays in config:
```yaml
scraping:
  min_delay: 2.0
  max_delay: 5.0
```

2. Add proxies:
```yaml
scraping:
  proxies:
    - "http://proxy1:8080"
```

3. Reduce scraping frequency:
```yaml
scraping:
  interval: 600  # 10 minutes
```

### High Memory Usage

1. Limit database size:
```sql
-- Delete old jobs
DELETE FROM jobs WHERE scraped_at < date('now', '-30 days');
VACUUM;
```

2. Reduce connection pool:
```yaml
scraping:
  connection_pool_size: 5
```

---

## 🛡️ Security Best Practices

1. **Never commit secrets:**
   - Add `.env` to `.gitignore`
   - Keep `config.yaml` private

2. **Use environment variables:**
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

3. **Restrict file permissions:**
```bash
chmod 600 config.yaml
chmod 600 .env
```

4. **Use a firewall:**
```bash
# Allow only SSH
sudo ufw allow ssh
sudo ufw enable
```

5. **Keep system updated:**
```bash
sudo apt update && sudo apt upgrade -y
```

---

## 📈 Performance Optimization

### For High-Volume Scraping

1. **Use connection pooling:**
```yaml
scraping:
  connection_pool_size: 20
```

2. **Optimize database:**
```sql
-- Add indexes
CREATE INDEX idx_title ON jobs(title);
CREATE INDEX idx_company ON jobs(company);
```

3. **Use caching:**
   - Implement Redis for deduplication
   - Cache scraped pages temporarily

4. **Distribute load:**
   - Run multiple instances with different queries
   - Use a message queue (RabbitMQ, Redis)

---

## 🔄 Updating the Bot

```bash
# Pull latest changes
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart job-scraper

# Or Docker
docker-compose restart
```

---

## 📝 Additional Tips

### Scraping Best Practices

1. **Respect robots.txt** - Check each site's policy
2. **Use reasonable delays** - Don't hammer servers
3. **Rotate User-Agents** - Already implemented
4. **Consider APIs** - Many sites offer official APIs
5. **Use proxies for scale** - Residential proxies work best

### Legal Considerations

- Scraping job sites may violate their Terms of Service
- Some countries have anti-scraping laws
- Consider using official APIs when available
- For production, consult legal counsel

### Alternative Solutions

- **Official APIs:** LinkedIn API, Indeed API (via RapidAPI)
- **Job Aggregators:** Adzuna API, The Muse API, GitHub Jobs
- **Scraping Services:** ScrapingBee, Bright Data, Oxylabs
- **RSS Feeds:** Some sites offer RSS feeds for jobs

---

## 🆘 Getting Help

1. **Check logs first:**
```bash
tail -f job_scraper.log
```

2. **Enable debug logging:**
```python
# In job_scraper.py, change:
logger.setLevel(logging.DEBUG)
```

3. **Test individual components:**
```python
# Test Telegram connection
python3 -c "from telegram import Bot; bot = Bot('YOUR_TOKEN'); print(bot.send_message('YOUR_CHAT_ID', 'Test'))"
```

4. **Common issues:**
   - Invalid bot token → Double-check @BotFather
   - Chat ID wrong → Use @userinfobot
   - Sites blocking → Add delays, use proxies
   - No jobs found → Adjust filters

---

## 📄 License

This is a personal project. Use responsibly and at your own risk.

**Remember:** Always respect website Terms of Service and robots.txt!

---

## 🎯 Quick Command Reference

```bash
# Start (systemd)
sudo systemctl start job-scraper

# Stop
sudo systemctl stop job-scraper

# Restart
sudo systemctl restart job-scraper

# View logs
sudo journalctl -u job-scraper -f

# Docker start
docker-compose up -d

# Docker logs
docker-compose logs -f

# View database
sqlite3 jobs.db "SELECT * FROM jobs ORDER BY scraped_at DESC LIMIT 5;"
```

Good luck with your job search! 🎉
