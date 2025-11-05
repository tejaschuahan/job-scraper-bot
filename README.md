# Job Scraper Bot

A high-performance, production-ready job scraping bot that monitors multiple job sites concurrently, intelligently deduplicates listings, and sends real-time notifications via Telegram.

## ✨ Features

### 🚀 Core Functionality
- **Multi-Site Scraping**: LinkedIn, Glassdoor, Google Jobs, Indeed
- **Concurrent Scraping**: Asynchronous execution for maximum speed
- **Smart Deduplication**: MD5 hashing prevents duplicate notifications
- **Real-Time Alerts**: Instant Telegram notifications for new jobs
- **Persistent Storage**: SQLite database with indexed queries

### 🛡️ Anti-Scraping Protection
- **User-Agent Rotation**: Pool of 8+ realistic browser agents
- **Proxy Support**: Rotating proxy support with automatic failover
- **Random Delays**: Configurable human-like request intervals
- **Retry Logic**: Exponential backoff for failed requests
- **Rate Limit Handling**: Automatic 429 error detection and backoff

### 🎯 Advanced Filtering
- **Keyword Matching**: Include/exclude keyword lists
- **Location Filtering**: Target specific locations or remote jobs
- **Salary Range**: Filter by minimum/maximum salary
- **Job Type**: Full-time, part-time, contract, etc.
- **Experience Level**: Junior, mid-level, senior filtering
- **Remote-Only Mode**: Show only remote positions

### 📊 Monitoring & Stats
- **Health Checks**: Automatic failure detection
- **Statistics Tracking**: Jobs scraped, found, filtered per site
- **Telegram Alerts**: Notifications on crashes or failures
- **Rotating Logs**: 10MB file size limit with 5 backups
- **Periodic Reports**: Daily/hourly summary statistics

### ⚙️ Configuration
- **YAML Config**: Easy-to-edit configuration file
- **Environment Variables**: Support for .env files
- **Flexible Queries**: Multiple search terms per run
- **Site Toggle**: Enable/disable individual sites
- **Custom Notifications**: Configurable message format

### 🚢 Deployment Ready
- **Docker Support**: Complete Dockerfile and docker-compose
- **Systemd Service**: Linux service file for 24/7 operation
- **Auto-Restart**: Crash recovery and automatic restart
- **Cloud Ready**: Deploy to AWS, GCP, DigitalOcean, etc.
- **Resource Efficient**: Low memory footprint (~100-200MB)

## 📋 Requirements

- Python 3.9+
- Telegram Bot Token
- Telegram Chat ID

## 🚀 Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure the bot:**
```bash
# Edit config.yaml with your settings
nano config.yaml

# Add your Telegram credentials
telegram:
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"
```

3. **Run the bot:**
```bash
python job_scraper.py
```

## 📖 Documentation

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions including:
- Getting Telegram credentials
- Linux VPS setup with systemd
- Docker deployment
- Cloud platform guides (AWS, GCP, DigitalOcean)
- Monitoring and troubleshooting
- Performance optimization

## ⚙️ Configuration Example

```yaml
search:
  queries:
    - "data analyst"
    - "python developer"
  default_location: "Remote"

sites:
  linkedin:
    enabled: true
  glassdoor:
    enabled: true
  indeed:
    enabled: true
  google_jobs:
    enabled: false

scraping:
  interval: 300  # 5 minutes
  min_delay: 1.0
  max_delay: 3.0

filters:
  include_keywords:
    - "python"
    - "sql"
  exclude_keywords:
    - "senior"
    - "manager"
  remote_only: true
```

## 🔍 How It Works

1. **Scraping Cycle**: Every N seconds (configurable), the bot:
   - Scrapes all enabled job sites concurrently
   - Extracts job details (title, company, URL, etc.)
   - Applies configured filters

2. **Deduplication**: 
   - Creates MD5 hash from title + company + URL
   - Checks against database of seen jobs
   - Only processes truly new listings

3. **Notification**:
   - Formats job details in Markdown
   - Sends to Telegram with apply link
   - Rate-limits to prevent flooding

4. **Monitoring**:
   - Tracks success/failure rates
   - Sends periodic statistics
   - Alerts on consecutive failures

## 🎯 Supported Sites

| Site | Status | Notes |
|------|--------|-------|
| **LinkedIn** | ✅ Working | Public job search (no auth required) |
| **Glassdoor** | ⚠️ Limited | Cloudflare protection may block |
| **Indeed** | ✅ Working | Most reliable, least blocking |
| **Google Jobs** | ⚠️ Limited | Aggressive bot detection |

### Important Notes

- **LinkedIn**: Works without authentication but has limitations. Consider official API for production.
- **Glassdoor**: Strong anti-bot measures. May need Selenium/Playwright or residential proxies.
- **Google Jobs**: Actively blocks scrapers. Use with caution or consider SerpAPI.
- **Indeed**: Most scraper-friendly but still has rate limits.

## 📊 Performance

- **Speed**: ~5-15 seconds per scraping cycle (4 sites)
- **Memory**: ~100-200MB RAM usage
- **CPU**: Minimal (<5% on modern systems)
- **Network**: ~5-20 KB/s depending on interval
- **Database**: Grows ~1MB per 1000 jobs

## 🛡️ Anti-Scraping Features Explained

### User-Agent Rotation
Randomly selects from pool of realistic browser User-Agents to appear as regular user traffic.

### Request Delays
Random delays between 1-3 seconds (configurable) prevent pattern detection and rate limiting.

### Retry Logic
Failed requests automatically retry up to 3 times with exponential backoff:
- 1st retry: 5s wait
- 2nd retry: 10s wait
- 3rd retry: 20s wait

### Proxy Support
Rotates through proxy list to distribute requests across multiple IP addresses.

## 🔧 Troubleshooting

### No Jobs Found
- Check if sites are enabled in config
- Verify search queries are relevant
- Review logs for scraping errors
- Check if filters are too restrictive

### Getting Blocked
- Increase min_delay and max_delay
- Add proxy servers
- Reduce scraping interval
- Enable fewer sites

### Bot Not Starting
- Verify Telegram credentials
- Check Python version (3.9+)
- Install all dependencies
- Review error logs

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed troubleshooting guide.

## 📝 Advanced Usage

### Using Proxies

```yaml
scraping:
  proxies:
    - "http://proxy1.example.com:8080"
    - "http://user:pass@proxy2.example.com:3128"
    - "socks5://127.0.0.1:9050"  # Tor
```

### Multiple Queries

```yaml
search:
  queries:
    - "data analyst"
    - "business analyst"
    - "data scientist"
    - "machine learning engineer"
```

### Custom Filters

```yaml
filters:
  include_keywords: ["python", "sql", "tableau"]
  exclude_keywords: ["senior", "lead", "principal"]
  locations: ["Remote", "New York", "San Francisco"]
  exclude_locations: ["India", "Philippines"]
  min_salary: 80000
  remote_only: true
```

## 🚢 Deployment Options

### 1. Local Machine
```bash
python job_scraper.py
```

### 2. Linux Server (systemd)
```bash
sudo systemctl start job-scraper
sudo systemctl enable job-scraper
```

### 3. Docker
```bash
docker-compose up -d
```

### 4. Cloud VM
- AWS EC2
- Google Cloud Compute Engine
- DigitalOcean Droplet
- Azure VM

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete instructions.

## 🔐 Security

- Never commit `config.yaml` with real credentials
- Use `.env` for sensitive values
- Restrict file permissions: `chmod 600 config.yaml`
- Use environment variables in production
- Keep system and dependencies updated

## 📄 License

Personal project - use at your own risk. Always respect website Terms of Service and robots.txt policies.

## ⚠️ Legal Disclaimer

Web scraping may violate Terms of Service of target websites. This tool is for educational purposes. Users are responsible for ensuring compliance with applicable laws and website policies.

**Recommendations:**
- Use official APIs when available
- Respect rate limits and robots.txt
- Consider commercial scraping services for production
- Consult legal counsel for commercial use

## 🤝 Contributing

This is a personal project, but feel free to fork and customize for your needs!

## 📞 Support

For issues and questions:
1. Check logs: `tail -f job_scraper.log`
2. Enable debug mode: Set logging level to DEBUG
3. Review [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section
4. Check database: `sqlite3 jobs.db`

## 🎯 Future Enhancements

Potential improvements:
- [ ] Web dashboard for monitoring
- [ ] Email notifications
- [ ] Webhook support
- [ ] Machine learning for job relevance
- [ ] Multi-language support
- [ ] Browser automation (Selenium/Playwright)
- [ ] API endpoint for job data
- [ ] Mobile app integration

## 📈 Stats Example

```
📊 Scraping Statistics

⏱ Runtime: 1 day, 2:34:15
🔄 Cycles: 287
📥 Total Scraped: 1,432
✨ New Jobs: 47
🔁 Duplicates: 1,385
🚫 Filtered: 238
❌ Errors: 3

Per-Site Stats:
Indeed: 456 scraped, 18 new, 0 errors
LinkedIn: 389 scraped, 15 new, 1 errors
Glassdoor: 298 scraped, 8 new, 2 errors
Google Jobs: 289 scraped, 6 new, 0 errors
```

---

**Happy Job Hunting! 🎉**

Remember to scrape responsibly and respect website policies!
