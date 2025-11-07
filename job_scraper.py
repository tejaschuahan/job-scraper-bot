import asyncio
import aiohttp
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.error import TelegramError
import sqlite3
import hashlib
import time
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
import logging
from logging.handlers import RotatingFileHandler
import random
import re
from urllib.parse import urlencode, quote_plus
import yaml
from pathlib import Path
import json
import os

# Import stealth scrapers
try:
    from stealth_scrapers import StealthBrowserScraper
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

# Configure logging with rotation
def setup_logging():
    """Setup logging with file rotation"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # File handler with rotation (10MB max, keep 5 backup files)
    file_handler = RotatingFileHandler(
        'job_scraper.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()


class UserAgentRotator:
    """Rotates through realistic browser User-Agent strings"""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    ]
    
    @classmethod
    def get_random(cls) -> str:
        """Get a random User-Agent string"""
        return random.choice(cls.USER_AGENTS)


class JobFilter:
    """Advanced filtering for job listings"""
    
    def __init__(self, config: Dict):
        self.include_keywords = [k.lower() for k in (config.get('include_keywords') or [])]
        self.exclude_keywords = [k.lower() for k in (config.get('exclude_keywords') or [])]
        self.locations = [l.lower() for l in (config.get('locations') or [])]
        self.exclude_locations = [l.lower() for l in (config.get('exclude_locations') or [])]
        self.min_salary = config.get('min_salary')
        self.max_salary = config.get('max_salary')
        self.job_types = [jt.lower() for jt in (config.get('job_types') or [])]
        self.experience_levels = [el.lower() for el in (config.get('experience_levels') or [])]
        self.remote_only = config.get('remote_only', False)
        
    def matches(self, job: Dict) -> bool:
        """Check if job matches all filter criteria"""
        title_lower = job.get('title', '').lower()
        description_lower = job.get('description', '').lower()
        company_lower = job.get('company', '').lower()
        location_lower = job.get('location', '').lower()
        
        # Combine text for keyword matching
        combined_text = f"{title_lower} {description_lower} {company_lower}"
        
        # Include keywords (at least one must match if specified)
        if self.include_keywords:
            if not any(keyword in combined_text for keyword in self.include_keywords):
                logger.debug(f"Filtered out (no include keywords): {job['title']}")
                return False
        
        # Exclude keywords (none should match)
        if self.exclude_keywords:
            if any(keyword in combined_text for keyword in self.exclude_keywords):
                logger.debug(f"Filtered out (exclude keyword found): {job['title']}")
                return False
        
        # Location filtering
        if self.locations:
            if not any(loc in location_lower for loc in self.locations):
                logger.debug(f"Filtered out (location mismatch): {job['title']} - {job.get('location')}")
                return False
        
        # Exclude locations
        if self.exclude_locations:
            if any(loc in location_lower for loc in self.exclude_locations):
                logger.debug(f"Filtered out (excluded location): {job['title']} - {job.get('location')}")
                return False
        
        # Remote filtering
        if self.remote_only:
            remote_keywords = ['remote', 'work from home', 'wfh', 'telecommute']
            if not any(keyword in combined_text or keyword in location_lower for keyword in remote_keywords):
                logger.debug(f"Filtered out (not remote): {job['title']}")
                return False
        
        # Salary filtering
        if self.min_salary or self.max_salary:
            salary = self._extract_salary(job.get('salary', ''))
            if salary:
                if self.min_salary and salary < self.min_salary:
                    logger.debug(f"Filtered out (salary too low): {job['title']}")
                    return False
                if self.max_salary and salary > self.max_salary:
                    logger.debug(f"Filtered out (salary too high): {job['title']}")
                    return False
        
        # Job type filtering
        if self.job_types:
            if not any(jt in combined_text or jt in location_lower for jt in self.job_types):
                logger.debug(f"Filtered out (job type mismatch): {job['title']}")
                return False
        
        # Experience level filtering
        if self.experience_levels:
            if not any(level in combined_text for level in self.experience_levels):
                logger.debug(f"Filtered out (experience level mismatch): {job['title']}")
                return False
        
        return True
    
    def _extract_salary(self, salary_str: str) -> Optional[int]:
        """Extract numeric salary from string (returns annual amount)"""
        if not salary_str:
            return None
        
        # Remove common symbols and text
        salary_str = salary_str.replace('$', '').replace(',', '').replace('k', '000').lower()
        
        # Extract numbers
        numbers = re.findall(r'\d+', salary_str)
        if numbers:
            salary = int(numbers[0])
            
            # Convert hourly to annual (assuming 40hrs/week, 52 weeks)
            if 'hour' in salary_str or 'hr' in salary_str:
                salary = salary * 40 * 52
            
            return salary
        
        return None


class StatsTracker:
    """Track scraping statistics"""
    
    def __init__(self):
        self.stats = {
            'total_scraped': 0,
            'new_jobs': 0,
            'duplicate_jobs': 0,
            'filtered_jobs': 0,
            'errors': 0,
            'cycles_completed': 0,
            'last_reset': datetime.now(),
            'site_stats': {}
        }
    
    def record_scraped(self, site: str, count: int):
        """Record scraped jobs from a site"""
        self.stats['total_scraped'] += count
        if site not in self.stats['site_stats']:
            self.stats['site_stats'][site] = {'scraped': 0, 'new': 0, 'errors': 0}
        self.stats['site_stats'][site]['scraped'] += count
    
    def record_new(self, site: str):
        """Record a new job found"""
        self.stats['new_jobs'] += 1
        if site in self.stats['site_stats']:
            self.stats['site_stats'][site]['new'] += 1
    
    def record_duplicate(self):
        """Record a duplicate job"""
        self.stats['duplicate_jobs'] += 1
    
    def record_filtered(self):
        """Record a filtered job"""
        self.stats['filtered_jobs'] += 1
    
    def record_error(self, site: str = None):
        """Record an error"""
        self.stats['errors'] += 1
        if site and site in self.stats['site_stats']:
            self.stats['site_stats'][site]['errors'] += 1
    
    def record_cycle(self):
        """Record a completed cycle"""
        self.stats['cycles_completed'] += 1
    
    def get_summary(self) -> str:
        """Get formatted stats summary"""
        runtime = datetime.now() - self.stats['last_reset']
        
        summary = f"""
📊 **Scraping Statistics**

⏱ Runtime: {runtime}
🔄 Cycles: {self.stats['cycles_completed']}
📥 Total Scraped: {self.stats['total_scraped']}
✨ New Jobs: {self.stats['new_jobs']}
🔁 Duplicates: {self.stats['duplicate_jobs']}
🚫 Filtered: {self.stats['filtered_jobs']}
❌ Errors: {self.stats['errors']}

**Per-Site Stats:**
"""
        for site, site_stats in self.stats['site_stats'].items():
            summary += f"\n`{site}:` {site_stats['scraped']} scraped, {site_stats['new']} new, {site_stats['errors']} errors"
        
        return summary
    
    def reset(self):
        """Reset statistics"""
        self.stats = {
            'total_scraped': 0,
            'new_jobs': 0,
            'duplicate_jobs': 0,
            'filtered_jobs': 0,
            'errors': 0,
            'cycles_completed': 0,
            'last_reset': datetime.now(),
            'site_stats': {}
        }


class JobScraper:
    def __init__(self, config: Dict):
        self.config = config
        # Override with environment variables if available or if placeholder is used
        bot_token = config['telegram']['bot_token']
        chat_id = config['telegram']['chat_id']
        
        # Check if values are placeholders or need env var override
        if bot_token.startswith('${') or os.getenv('TELEGRAM_BOT_TOKEN'):
            config['telegram']['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN', bot_token)
        if chat_id.startswith('${') or os.getenv('TELEGRAM_CHAT_ID'):
            config['telegram']['chat_id'] = os.getenv('TELEGRAM_CHAT_ID', chat_id)
        
        self.telegram_token = config['telegram']['bot_token']
        self.chat_id = config['telegram']['chat_id']
        self.bot = Bot(token=self.telegram_token)
        self.db_path = config.get('database', {}).get('path', 'jobs.db')
        self.session = None
        self.seen_jobs: Set[str] = set()
        self.job_filter = JobFilter(config.get('filters', {}))
        self.stats = StatsTracker()
        
        # Initialize Gemini AI (optional)
        self.gemini = None
        self.job_discovery = None
        gemini_config = config.get('gemini', {})
        if gemini_config.get('enabled', False):
            try:
                from gemini_ai import get_gemini_ai
                from gemini_job_discovery import get_job_discovery
                self.gemini = get_gemini_ai()
                if self.gemini:
                    logger.info("✨ Gemini AI features enabled")
                    self.job_discovery = get_job_discovery(self.gemini)
                    if self.job_discovery:
                        logger.info("🔍 Gemini Job Discovery enabled")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize Gemini AI: {e}")
        
        # Anti-scraping settings
        self.min_delay = config.get('scraping', {}).get('min_delay', 1)
        self.max_delay = config.get('scraping', {}).get('max_delay', 3)
        self.max_retries = config.get('scraping', {}).get('max_retries', 3)
        self.retry_delay = config.get('scraping', {}).get('retry_delay', 5)
        
        # Proxy settings
        self.proxies = config.get('scraping', {}).get('proxies', [])
        self.current_proxy_index = 0
        
        # Stealth mode settings
        self.use_stealth = config.get('scraping', {}).get('use_stealth_mode', False)
        self.stealth_scraper = None
        
        # Health check
        self.last_successful_scrape = datetime.now()
        self.consecutive_failures = 0
        self.max_consecutive_failures = config.get('monitoring', {}).get('max_consecutive_failures', 5)
        
        self._init_db()
        self._load_seen_jobs()
        
    def _init_db(self):
        """Initialize SQLite database for job tracking"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                job_hash TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                url TEXT,
                location TEXT,
                salary TEXT,
                job_type TEXT,
                description TEXT,
                site TEXT,
                scraped_at TIMESTAMP
            )
        ''')
        
        # Create index for faster queries
        c.execute('CREATE INDEX IF NOT EXISTS idx_scraped_at ON jobs(scraped_at)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_site ON jobs(site)')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def _load_seen_jobs(self):
        """Load previously seen jobs from database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Only load jobs from last 30 days to keep set manageable
        cutoff_date = datetime.now() - timedelta(days=30)
        c.execute('SELECT job_hash FROM jobs WHERE scraped_at > ?', (cutoff_date,))
        self.seen_jobs = {row[0] for row in c.fetchall()}
        conn.close()
        logger.info(f"Loaded {len(self.seen_jobs)} previously seen jobs from last 30 days")
    
    def _hash_job(self, job: Dict) -> str:
        """Create unique hash for job to avoid duplicates"""
        # Normalize title and company for better deduplication
        title = re.sub(r'[^\w\s]', '', job['title'].lower()).strip()
        company = re.sub(r'[^\w\s]', '', job['company'].lower()).strip()
        
        # Remove common variations
        title = title.replace('junior', '').replace('senior', '').replace('entry level', '').strip()
        title = re.sub(r'\s+', ' ', title)  # Normalize spaces
        
        # Use title, company for main uniqueness
        # URL as secondary (some sites post same job multiple times with different URLs)
        url_normalized = job['url'].split('?')[0].split('#')[0]  # Remove query params and anchors
        unique_str = f"{title}||{company}||{url_normalized}"
        return hashlib.md5(unique_str.encode()).hexdigest()
    
    def _is_similar_job(self, job1: Dict, job2: Dict) -> bool:
        """Check if two jobs are similar (likely duplicates)"""
        # Normalize titles for comparison
        title1 = re.sub(r'[^\w\s]', '', job1['title'].lower()).strip()
        title2 = re.sub(r'[^\w\s]', '', job2['title'].lower()).strip()
        
        # Same company and very similar titles = duplicate
        if job1['company'].lower() == job2['company'].lower():
            # Calculate simple word overlap
            words1 = set(title1.split())
            words2 = set(title2.split())
            if len(words1) > 0 and len(words2) > 0:
                overlap = len(words1 & words2) / min(len(words1), len(words2))
                if overlap > 0.7:  # 70% word overlap
                    return True
        
        return False
    
    def _save_job(self, job: Dict, job_hash: str):
        """Save job to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO jobs (job_hash, title, company, url, location, salary, 
                                  job_type, description, site, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (job_hash, job['title'], job['company'], job['url'], 
                  job.get('location', ''), job.get('salary', ''),
                  job.get('job_type', ''), job.get('description', ''),
                  job['site'], datetime.now()))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Job already exists
        finally:
            conn.close()
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy from rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy
    
    async def fetch_with_retry(self, url: str, site: str, **kwargs) -> Optional[str]:
        """Fetch URL with retry logic and exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                # Random delay to appear more human-like
                delay = random.uniform(self.min_delay, self.max_delay)
                await asyncio.sleep(delay)
                
                # Rotate User-Agent and add comprehensive headers
                headers = kwargs.get('headers', {})
                headers['User-Agent'] = UserAgentRotator.get_random()
                headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
                headers['Accept-Language'] = 'en-US,en;q=0.9'
                headers['Accept-Encoding'] = 'gzip, deflate, br'
                headers['DNT'] = '1'
                headers['Connection'] = 'keep-alive'
                headers['Upgrade-Insecure-Requests'] = '1'
                headers['Sec-Fetch-Dest'] = 'document'
                headers['Sec-Fetch-Mode'] = 'navigate'
                headers['Sec-Fetch-Site'] = 'none'
                headers['Cache-Control'] = 'max-age=0'
                kwargs['headers'] = headers
                
                # Add proxy if available
                proxy = self.get_next_proxy()
                if proxy:
                    kwargs['proxy'] = proxy
                
                async with self.session.get(url, **kwargs) as response:
                    if response.status == 200:
                        self.consecutive_failures = 0
                        return await response.text()
                    elif response.status == 429:  # Rate limited
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Rate limited on {site}, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                    elif response.status == 403:  # Forbidden
                        logger.warning(f"403 Forbidden on {site}, attempt {attempt + 1}")
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    else:
                        logger.warning(f"HTTP {response.status} on {site}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on {site}, attempt {attempt + 1}")
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
            except Exception as e:
                logger.error(f"Error fetching {site}: {e}, attempt {attempt + 1}")
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
        
        # All retries failed
        self.consecutive_failures += 1
        self.stats.record_error(site)
        
        # Alert if too many consecutive failures
        if self.consecutive_failures >= self.max_consecutive_failures:
            await self.send_alert(f"⚠️ WARNING: {self.consecutive_failures} consecutive scraping failures!")
        
        return None
    
    async def send_telegram_message(self, job: Dict):
        """Send job notification to Telegram"""
        # Get notification format from config
        format_config = self.config.get('telegram', {}).get('notification_format', {})
        gemini_config = self.config.get('gemini', {})
        
        # Get AI summary and score if enabled
        ai_summary = None
        quality_score = None
        salary_estimate = None
        company_insights = None
        competition_info = None
        
        if self.gemini and gemini_config.get('features', {}).get('job_summarization', False):
            try:
                ai_summary = self.gemini.summarize_job(job)
            except Exception as e:
                logger.warning(f"Failed to generate AI summary: {e}")
        
        if self.gemini and gemini_config.get('features', {}).get('job_quality_scoring', False):
            try:
                score_data = self.gemini.score_job_quality(job)
                quality_score = score_data.get('score')
            except Exception as e:
                logger.warning(f"Failed to score job quality: {e}")
        
        # Estimate salary if not provided
        if self.gemini and not job.get('salary'):
            try:
                salary_estimate = self.gemini.estimate_salary(job)
            except Exception as e:
                logger.warning(f"Failed to estimate salary: {e}")
        
        # Get company insights
        if self.gemini and gemini_config.get('features', {}).get('company_analysis', True):
            try:
                company_insights = self.gemini.analyze_company(job.get('company', ''))
            except Exception as e:
                logger.warning(f"Failed to analyze company: {e}")
        
        # Estimate competition
        if self.gemini and gemini_config.get('features', {}).get('competition_analysis', False):
            try:
                competition_info = self.gemini.estimate_competition(job)
            except Exception as e:
                logger.warning(f"Failed to estimate competition: {e}")
        
        # Escape Markdown special characters to avoid parsing errors
        def escape_markdown(text: str) -> str:
            """Escape special Markdown characters"""
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')
            return text
        
        # Build message based on config
        quality_emoji = ""
        if quality_score:
            if quality_score >= 8:
                quality_emoji = " 🌟"
            elif quality_score >= 6:
                quality_emoji = " ⭐"
        
        message_parts = [f"🔔 **New Job Alert\\!**{quality_emoji}\n"]
        
        if format_config.get('show_title', True):
            message_parts.append(f"**Title:** {escape_markdown(job['title'])}")
        
        if format_config.get('show_company', True):
            message_parts.append(f"**Company:** {escape_markdown(job['company'])}")
        
        if format_config.get('show_location', True) and job.get('location'):
            message_parts.append(f"📍 **Location:** {escape_markdown(job['location'])}")
        
        # Show salary (actual or estimated)
        if format_config.get('show_salary', True):
            if job.get('salary'):
                message_parts.append(f"💰 **Salary:** {escape_markdown(job['salary'])}")
            elif salary_estimate and salary_estimate.get('salary_min', 0) > 0:
                salary_range = f"{salary_estimate['salary_min']}-{salary_estimate['salary_max']} LPA"
                confidence = salary_estimate.get('confidence', 'Medium')
                message_parts.append(f"💰 **Est\\. Salary:** {escape_markdown(salary_range)} \\({escape_markdown(confidence)} confidence\\)")
        
        if format_config.get('show_job_type', False) and job.get('job_type'):
            message_parts.append(f"📋 **Type:** {escape_markdown(job['job_type'])}")
        
        # Show company insights if available
        if company_insights and company_insights.get('type') != 'Unknown':
            company_type = company_insights.get('type', '')
            salary_rep = company_insights.get('salary_reputation', '')
            if company_type:
                message_parts.append(f"🏢 **Company:** {escape_markdown(company_type)}")
            if salary_rep and salary_rep != 'Unknown':
                message_parts.append(f"💼 **Pay Reputation:** {escape_markdown(salary_rep)}")
        
        if format_config.get('show_site', True):
            message_parts.append(f"**Site:** {escape_markdown(job['site'])}")
        
        # Add AI-generated summary if available
        if ai_summary:
            message_parts.append(f"\n✨ **AI Summary:**")
            # Escape the AI summary
            for line in ai_summary.split('\n'):
                if line.strip():
                    message_parts.append(escape_markdown(line))
        elif format_config.get('show_description', False) and job.get('description'):
            # Fallback to regular description if no AI summary
            desc = job['description'][:200] + "..." if len(job['description']) > 200 else job['description']
            desc = escape_markdown(desc)
            message_parts.append(f"\n{desc}")
        
        # Add quality score if available
        if quality_score:
            score_text = f"Quality Score: {quality_score}/10"
            message_parts.append(f"\n📊 {escape_markdown(score_text)}")
        
        # Add competition info if available
        if competition_info and competition_info.get('competition'):
            comp_level = competition_info.get('competition', 'Medium')
            applicants = competition_info.get('estimated_applicants', '')
            if comp_level != 'Medium':  # Only show if not default
                message_parts.append(f"👥 **Competition:** {escape_markdown(comp_level)}")
            if competition_info.get('quick_apply_advantage'):
                message_parts.append(f"⚡ **Tip:** Apply quickly for better visibility\\!")
        
        # URL doesn't need escaping in link format
        message_parts.append(f"\n🔗 [Apply Here]({job['url']})")
        
        message = "\n".join(message_parts)
        
        try:
            # Use chat_id from config (allows per-user messaging in interactive mode)
            chat_id = self.config.get('telegram', {}).get('chat_id', self.chat_id)
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='MarkdownV2',  # Use MarkdownV2 with escaped characters
                disable_web_page_preview=format_config.get('disable_preview', False)
            )
            logger.info(f"[SENT] {job['title']} at {job['company']} to user {chat_id}")
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
            self.stats.record_error()
    
    async def send_alert(self, message: str):
        """Send alert message to Telegram"""
        try:
            # Use chat_id from config (allows per-user messaging in interactive mode)
            chat_id = self.config.get('telegram', {}).get('chat_id', self.chat_id)
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except TelegramError as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def send_stats_summary(self):
        """Send statistics summary to Telegram"""
        summary = self.stats.get_summary()
        try:
            # Use chat_id from config (allows per-user messaging in interactive mode)
            chat_id = self.config.get('telegram', {}).get('chat_id', self.chat_id)
            await self.bot.send_message(
                chat_id=chat_id,
                text=summary,
                parse_mode='Markdown'
            )
            logger.info(f"Sent statistics summary to user {chat_id}")
        except TelegramError as e:
            logger.error(f"Failed to send stats: {e}")
    
    # ========== SITE-SPECIFIC SCRAPERS ==========
    
    async def scrape_linkedin(self, query: str) -> List[Dict]:
        """
        Scrape LinkedIn job listings
        
        Note: LinkedIn has strong anti-scraping measures. This scraper accesses
        the public job search page which doesn't require authentication but has
        limitations. For production, consider using LinkedIn's official API or
        a service like Bright Data.
        
        CSS Selectors:
        - Job cards: 'li.jobs-search__results-list > li' or 'div.base-card'
        - Title: 'h3.base-search-card__title'
        - Company: 'h4.base-search-card__subtitle'
        - Location: 'span.job-search-card__location'
        - Link: 'a.base-card__full-link'
        """
        jobs = []
        site = "LinkedIn"
        
        # LinkedIn public job search URL
        params = {
            'keywords': query,
            'location': self.config.get('search', {}).get('default_location', ''),
            'f_TPR': 'r86400',  # Last 24 hours
            'position': 1,
            'pageNum': 0
        }
        url = f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"
        
        logger.info(f"Scraping {site} for: {query}")
        html = await self.fetch_with_retry(url, site, timeout=aiohttp.ClientTimeout(total=15))
        
        if not html:
            logger.warning(f"Failed to fetch {site}")
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try multiple selectors as LinkedIn changes them frequently
            job_cards = soup.find_all('div', class_='base-card') or \
                       soup.find_all('div', class_='job-search-card') or \
                       soup.select('li.jobs-search__results-list > li')
            
            logger.debug(f"Found {len(job_cards)} job cards on {site}")
            
            for card in job_cards[:20]:  # Limit to prevent overwhelming
                try:
                    # Extract job details
                    title_elem = card.find('h3', class_='base-search-card__title') or \
                                card.find('h3', class_='job-search-card__title')
                    
                    company_elem = card.find('h4', class_='base-search-card__subtitle') or \
                                  card.find('h4', class_='job-search-card__company-name')
                    
                    location_elem = card.find('span', class_='job-search-card__location')
                    
                    link_elem = card.find('a', class_='base-card__full-link') or \
                               card.find('a', class_='job-search-card__link')
                    
                    if not (title_elem and company_elem and link_elem):
                        continue
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True),
                        'url': link_elem['href'].split('?')[0],  # Remove tracking params
                        'location': location_elem.get_text(strip=True) if location_elem else 'Not specified',
                        'site': site,
                        'description': ''
                    }
                    
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job card: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error parsing {site} HTML: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_linkedin_posts(self, query: str) -> List[Dict]:
        """
        Scrape LinkedIn posts containing job listings
        
        This scraper searches LinkedIn posts/feed for job-related content.
        Many companies post job openings as regular posts which don't appear
        in the jobs section. Searches for posts with keywords like:
        "hiring", "we're hiring", "job opening", "career opportunity", etc.
        
        CSS Selectors:
        - Post containers: 'div.feed-shared-update-v2'
        - Post text: 'div.feed-shared-text' or 'span.break-words'
        - Author: 'span.feed-shared-actor__name'
        - Post link: 'a.app-aware-link'
        
        Note: LinkedIn requires authentication for full post access.
        This searches public posts visible to non-authenticated users.
        """
        jobs = []
        site = "LinkedIn Posts"
        
        # Build search query for job-related posts
        job_keywords = ["hiring", "we're hiring", "job opening", "career opportunity", 
                       "join our team", "now hiring", "apply now"]
        
        # Combine query with job keywords
        search_query = f"{query} ({' OR '.join(job_keywords)})"
        query_encoded = quote_plus(search_query)
        
        # LinkedIn search for posts/content
        url = f"https://www.linkedin.com/search/results/content/?keywords={query_encoded}&origin=GLOBAL_SEARCH_HEADER&sid=xYt"
        
        logger.info(f"Scraping {site} for: {query}")
        html = await self.fetch_with_retry(url, site, timeout=aiohttp.ClientTimeout(total=15))
        
        if not html:
            logger.warning(f"Failed to fetch {site}")
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # LinkedIn post containers
            post_cards = soup.find_all('div', class_='feed-shared-update-v2') or \
                        soup.find_all('li', class_='reusable-search__result-container') or \
                        soup.find_all('div', class_='search-result__wrapper')
            
            logger.debug(f"Found {len(post_cards)} posts on {site}")
            
            for card in post_cards[:15]:  # Limit posts to check
                try:
                    # Extract post content
                    text_elem = card.find('div', class_='feed-shared-text') or \
                               card.find('span', class_='break-words') or \
                               card.find('div', class_='update-components-text')
                    
                    # Extract author/company
                    author_elem = card.find('span', class_='feed-shared-actor__name') or \
                                 card.find('span', class_='entity-result__title-text') or \
                                 card.find('div', class_='update-components-actor__name')
                    
                    # Extract post link
                    link_elem = card.find('a', class_='app-aware-link') or \
                               card.find('a', {'data-control-name': 'search_srp_result'}) or \
                               card.find('a', class_='update-components-actor__container-link')
                    
                    if not (text_elem and author_elem):
                        continue
                    
                    post_text = text_elem.get_text(strip=True)
                    
                    # Check if post mentions hiring/job keywords
                    post_lower = post_text.lower()
                    has_hiring_keyword = any(keyword in post_lower for keyword in 
                                            ["hiring", "job opening", "career", "join our team", 
                                             "now hiring", "apply", "vacancy", "position"])
                    
                    if not has_hiring_keyword:
                        continue
                    
                    # Try to extract job title from post text
                    title = ""
                    # Look for patterns like "Hiring: Data Analyst" or "Data Analyst - Join us"
                    title_patterns = [
                        r'hiring[:\s]+([A-Z][a-zA-Z\s]+?)(?:\s*[-|–]|\s*at|\s*@|\s*$)',
                        r'(?:role|position)[:\s]+([A-Z][a-zA-Z\s]+?)(?:\s*[-|–]|\s*at|\s*@|\s*$)',
                        r'(?:looking for|seeking)[:\s]+([A-Z][a-zA-Z\s]+?)(?:\s*[-|–]|\s*at|\s*@|\s*$)',
                    ]
                    
                    import re
                    for pattern in title_patterns:
                        match = re.search(pattern, post_text[:200])  # Check first 200 chars
                        if match:
                            title = match.group(1).strip()
                            break
                    
                    # Fallback: use query as title if no specific title found
                    if not title or len(title) < 3:
                        title = f"{query.title()} - Hiring Post"
                    
                    post_url = ''
                    if link_elem and link_elem.get('href'):
                        post_url = link_elem['href']
                        if not post_url.startswith('http'):
                            post_url = f"https://www.linkedin.com{post_url}"
                    
                    # Extract company name or author
                    company = author_elem.get_text(strip=True)
                    
                    # Clean up post snippet (first 200 chars)
                    description = post_text[:200] + "..." if len(post_text) > 200 else post_text
                    
                    job = {
                        'title': title[:100],  # Limit length
                        'company': company,
                        'url': post_url.split('?')[0] if post_url else f"https://www.linkedin.com/search/results/content/?keywords={query_encoded}",
                        'location': 'Remote/LinkedIn Post',
                        'site': site,
                        'description': description
                    }
                    
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} post: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error parsing {site} HTML: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_glassdoor(self, query: str) -> List[Dict]:
        """
        Scrape Glassdoor job listings
        
        Glassdoor has aggressive anti-bot measures including:
        - Cloudflare protection
        - IP-based rate limiting
        - Session/cookie requirements
        
        CSS Selectors:
        - Job cards: 'li.react-job-listing' or 'article.job-tile'
        - Title: 'a.job-title' or data-test="job-link"
        - Company: 'div.employer-name'
        - Location: 'div.location'
        - Salary: 'span.salary-estimate'
        
        For production: Consider using Selenium/Playwright with stealth plugins
        or a scraping service.
        """
        jobs = []
        site = "Glassdoor"
        
        # Glassdoor job search URL
        query_encoded = quote_plus(query)
        location = self.config.get('search', {}).get('default_location', '')
        location_encoded = quote_plus(location) if location else ''
        
        url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query_encoded}"
        if location_encoded:
            url += f"&locT=C&locId=1&locKeyword={location_encoded}"
        
        logger.info(f"Scraping {site} for: {query}")
        html = await self.fetch_with_retry(
            url, 
            site, 
            timeout=aiohttp.ClientTimeout(total=20),
            headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        if not html:
            logger.warning(f"Failed to fetch {site}")
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try multiple selectors
            job_cards = soup.find_all('li', class_='react-job-listing') or \
                       soup.find_all('article', attrs={'data-test': 'jobListing'}) or \
                       soup.find_all('li', class_='jl')
            
            logger.debug(f"Found {len(job_cards)} job cards on {site}")
            
            for card in job_cards[:20]:
                try:
                    # Try various selector patterns
                    title_elem = card.find('a', attrs={'data-test': 'job-link'}) or \
                                card.find('a', class_='job-title') or \
                                card.find('a', class_='jobLink')
                    
                    company_elem = card.find('div', attrs={'data-test': 'employer-name'}) or \
                                  card.find('div', class_='employer-name') or \
                                  card.find('span', class_='jobEmpolyerName')
                    
                    location_elem = card.find('div', attrs={'data-test': 'emp-location'}) or \
                                   card.find('div', class_='location') or \
                                   card.find('span', class_='loc')
                    
                    salary_elem = card.find('span', attrs={'data-test': 'detailSalary'}) or \
                                 card.find('span', class_='salary-estimate')
                    
                    if not (title_elem and company_elem):
                        continue
                    
                    # Extract job URL
                    job_url = title_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.glassdoor.com{job_url}"
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True),
                        'url': job_url.split('?')[0],
                        'location': location_elem.get_text(strip=True) if location_elem else 'Not specified',
                        'salary': salary_elem.get_text(strip=True) if salary_elem else '',
                        'site': site,
                        'description': ''
                    }
                    
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job card: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error parsing {site} HTML: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_google_jobs(self, query: str) -> List[Dict]:
        """
        Scrape Google for Jobs (aggregator)
        
        Google for Jobs aggregates listings from many sources. This scraper
        accesses the search results page which shows job cards.
        
        Note: Google actively blocks scrapers. For production use:
        - Residential proxies
        - Selenium/Playwright with stealth
        - Google Jobs API (via third-party services like SerpAPI)
        
        CSS Selectors:
        - Job cards: 'div.PwjeAc' or 'li.iFjolb'
        - Title: 'div.BjJfJf'
        - Company: 'div.vNEEBe'
        - Location: 'div.Qk80Jf'
        """
        jobs = []
        site = "Google Jobs"
        
        # Google Jobs search URL
        query_encoded = quote_plus(f"{query} jobs")
        location = self.config.get('search', {}).get('default_location', '')
        if location:
            query_encoded = quote_plus(f"{query} jobs {location}")
        
        url = f"https://www.google.com/search?q={query_encoded}&ibp=htl;jobs"
        
        logger.info(f"Scraping {site} for: {query}")
        html = await self.fetch_with_retry(
            url,
            site,
            timeout=aiohttp.ClientTimeout(total=15),
            headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
        )
        
        if not html:
            logger.warning(f"Failed to fetch {site}")
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Google's job cards (selectors change frequently)
            job_cards = soup.find_all('div', class_='PwjeAc') or \
                       soup.find_all('li', class_='iFjolb')
            
            logger.debug(f"Found {len(job_cards)} job cards on {site}")
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('div', class_='BjJfJf') or \
                                card.find('h2', class_='KLsYvd')
                    
                    company_elem = card.find('div', class_='vNEEBe')
                    
                    location_elem = card.find('div', class_='Qk80Jf')
                    
                    # Job link might be in data attribute or anchor tag
                    link_elem = card.find('a', class_='pMhGee') or \
                               card.find('a')
                    
                    if not (title_elem and company_elem):
                        continue
                    
                    job_url = ''
                    if link_elem and link_elem.get('href'):
                        job_url = link_elem['href']
                        if job_url.startswith('/url?q='):
                            # Extract actual URL from Google redirect
                            job_url = job_url.split('/url?q=')[1].split('&')[0]
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True),
                        'url': job_url or f"https://www.google.com/search?q={query_encoded}&ibp=htl;jobs",
                        'location': location_elem.get_text(strip=True) if location_elem else 'Not specified',
                        'site': site,
                        'description': ''
                    }
                    
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job card: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error parsing {site} HTML: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_indeed(self, query: str) -> List[Dict]:
        """
        Scrape Indeed.com job listings
        
        Indeed is relatively scraper-friendly but implements:
        - Rate limiting (429 errors after ~100 requests)
        - Basic bot detection
        - Pagination via 'start' parameter
        
        CSS Selectors:
        - Job cards: 'div.job_seen_beacon' or 'div.slider_container'
        - Title: 'h2.jobTitle' or 'a.jcs-JobTitle'
        - Company: 'span.companyName'
        - Location: 'div.companyLocation'
        - Salary: 'div.salary-snippet'
        """
        jobs = []
        site = "Indeed"
        
        # Indeed search URL - simpler format
        location = self.config.get('search', {}).get('default_location', '')
        query_encoded = query.replace(' ', '+')
        location_encoded = location.replace(' ', '+') if location else ''
        
        # Build URL without urlencode to avoid double encoding
        url = f"https://www.indeed.com/jobs?q={query_encoded}"
        if location_encoded:
            url += f"&l={location_encoded}"
        url += "&fromage=1&sort=date"
        
        logger.info(f"Scraping {site} for: {query}")
        html = await self.fetch_with_retry(url, site, timeout=aiohttp.ClientTimeout(total=15))
        
        if not html:
            logger.warning(f"Failed to fetch {site}")
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Indeed job cards
            job_cards = soup.find_all('div', class_='job_seen_beacon') or \
                       soup.find_all('div', class_='slider_container') or \
                       soup.find_all('td', class_='resultContent')
            
            logger.debug(f"Found {len(job_cards)} job cards on {site}")
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('h2', class_='jobTitle') or \
                                card.find('a', class_='jcs-JobTitle')
                    
                    company_elem = card.find('span', class_='companyName')
                    
                    location_elem = card.find('div', class_='companyLocation')
                    
                    salary_elem = card.find('div', class_='salary-snippet') or \
                                 card.find('div', class_='metadata salary-snippet-container')
                    
                    link_elem = card.find('a', class_='jcs-JobTitle') or \
                               title_elem.find('a') if title_elem else None
                    
                    if not (title_elem and company_elem and link_elem):
                        continue
                    
                    job_url = link_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.indeed.com{job_url}"
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True),
                        'url': job_url.split('?')[0],
                        'location': location_elem.get_text(strip=True) if location_elem else 'Not specified',
                        'salary': salary_elem.get_text(strip=True) if salary_elem else '',
                        'site': site,
                        'description': ''
                    }
                    
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job card: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error parsing {site} HTML: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_bing_jobs(self, query: str) -> List[Dict]:
        """
        Scrape Bing for Jobs
        
        Bing has more lenient scraping policies than Google and provides
        a job search feature similar to Google Jobs. Less aggressive blocking.
        
        CSS Selectors:
        - Job cards: 'li.job-card' or 'div.job-item'
        - Title: 'h2.job-title' or 'a.job-card-title'
        - Company: 'div.job-card-company' or 'span.company'
        - Location: 'div.job-card-location'
        """
        jobs = []
        site = "Bing Jobs"
        
        # Bing Jobs search URL
        location = self.config.get('search', {}).get('default_location', 'Delhi')
        query_encoded = quote_plus(f"{query} jobs in {location}")
        
        url = f"https://www.bing.com/jobs?q={query_encoded}&location={quote_plus(location)}"
        
        logger.info(f"Scraping {site} for: {query}")
        html = await self.fetch_with_retry(
            url,
            site,
            timeout=aiohttp.ClientTimeout(total=15),
            headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
        )
        
        if not html:
            logger.warning(f"Failed to fetch {site}")
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Bing job cards (multiple possible selectors)
            job_cards = soup.find_all('li', class_='job-card') or \
                       soup.find_all('div', class_='job-item') or \
                       soup.find_all('article', class_='job') or \
                       soup.find_all('div', {'data-testid': 'job-card'})
            
            logger.debug(f"Found {len(job_cards)} job cards on {site}")
            
            for card in job_cards[:20]:
                try:
                    # Try multiple selectors for each field
                    title_elem = card.find('h2', class_='job-title') or \
                                card.find('a', class_='job-card-title') or \
                                card.find('h3') or \
                                card.find('a', {'data-testid': 'job-title'})
                    
                    company_elem = card.find('div', class_='job-card-company') or \
                                  card.find('span', class_='company') or \
                                  card.find('div', class_='company-name') or \
                                  card.find('span', {'data-testid': 'company-name'})
                    
                    location_elem = card.find('div', class_='job-card-location') or \
                                   card.find('span', class_='location') or \
                                   card.find('div', class_='job-location')
                    
                    salary_elem = card.find('div', class_='salary') or \
                                 card.find('span', class_='job-salary')
                    
                    link_elem = card.find('a', class_='job-card-title') or \
                               card.find('a') or \
                               title_elem.find('a') if title_elem else None
                    
                    if not (title_elem and company_elem):
                        continue
                    
                    job_url = ''
                    if link_elem and link_elem.get('href'):
                        job_url = link_elem['href']
                        if not job_url.startswith('http'):
                            job_url = f"https://www.bing.com{job_url}"
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True),
                        'url': job_url or url,
                        'location': location_elem.get_text(strip=True) if location_elem else location,
                        'salary': salary_elem.get_text(strip=True) if salary_elem else '',
                        'site': site,
                        'description': ''
                    }
                    
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job card: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error parsing {site} HTML: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    # ========== MAIN SCRAPING LOGIC ==========
    
    async def scrape_remotive(self, query: str) -> List[Dict]:
        """
        Scrape Remotive.io API - Free, reliable, no API key needed!
        Focuses on remote jobs from tech companies.
        """
        jobs = []
        site = "Remotive"
        
        url = "https://remotive.com/api/remote-jobs"
        
        logger.info(f"Scraping {site} for: {query}")
        
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    query_lower = query.lower()
                    for job_data in data.get('jobs', [])[:50]:  # Limit to 50
                        title = job_data.get('title', '').lower()
                        description = job_data.get('description', '').lower()
                        category = job_data.get('category', '').lower()
                        
                        # Filter by query in title, description, or category
                        if query_lower in title or query_lower in description or query_lower in category:
                            job = {
                                'title': job_data.get('title', ''),
                                'company': job_data.get('company_name', ''),
                                'url': job_data.get('url', ''),
                                'location': 'Remote',
                                'salary': job_data.get('salary', ''),
                                'job_type': job_data.get('job_type', ''),
                                'description': job_data.get('description', '')[:300],
                                'site': site
                            }
                            jobs.append(job)
                    
                    self.stats.record_scraped(site, len(jobs))
                    logger.info(f"Scraped {len(jobs)} jobs from {site}")
        except Exception as e:
            logger.error(f"Error scraping {site}: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    # ========== STEALTH MODE SCRAPERS (Browser-based) ==========
    
    async def scrape_indeed_stealth(self, query: str) -> List[Dict]:
        """Scrape Indeed using stealth browser"""
        if not self.use_stealth or not STEALTH_AVAILABLE:
            return await self.scrape_indeed(query)
        
        try:
            location = self.config.get('search', {}).get('default_location', '')
            jobs = await self.stealth_scraper.scrape_indeed_stealth(query, location)
            self.stats.record_scraped('Indeed', len(jobs))
            return jobs
        except Exception as e:
            logger.error(f"Stealth Indeed scraper failed: {e}")
            self.stats.record_error('Indeed')
            return []
    
    async def scrape_glassdoor_stealth(self, query: str) -> List[Dict]:
        """Scrape Glassdoor using stealth browser"""
        if not self.use_stealth or not STEALTH_AVAILABLE:
            return await self.scrape_glassdoor(query)
        
        try:
            location = self.config.get('search', {}).get('default_location', '')
            jobs = await self.stealth_scraper.scrape_glassdoor_stealth(query, location)
            self.stats.record_scraped('Glassdoor', len(jobs))
            return jobs
        except Exception as e:
            logger.error(f"Stealth Glassdoor scraper failed: {e}")
            self.stats.record_error('Glassdoor')
            return []
    
    async def scrape_google_jobs_stealth(self, query: str) -> List[Dict]:
        """Scrape Google Jobs using stealth browser"""
        if not self.use_stealth or not STEALTH_AVAILABLE:
            return await self.scrape_google_jobs(query)
        
        try:
            location = self.config.get('search', {}).get('default_location', '')
            jobs = await self.stealth_scraper.scrape_google_jobs_stealth(query, location)
            self.stats.record_scraped('Google Jobs', len(jobs))
            return jobs
        except Exception as e:
            logger.error(f"Stealth Google Jobs scraper failed: {e}")
            self.stats.record_error('Google Jobs')
            return []
    
    # ========== INDIAN JOB SITES ==========
    
    async def scrape_naukri(self, query: str) -> List[Dict]:
        """Scrape Naukri.com - India's largest job portal"""
        from urllib.parse import quote_plus
        
        jobs = []
        site = "Naukri"
        location = self.config.get('search', {}).get('default_location', 'India')
        
        # Naukri URL format
        query_encoded = quote_plus(query)
        url = f"https://www.naukri.com/{query_encoded}-jobs"
        
        logger.info(f"Scraping {site} for: {query}")
        
        html = await self.fetch_with_retry(url, site)
        if not html:
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            job_cards = soup.find_all('article', class_='jobTuple')
            
            for card in job_cards[:20]:  # Limit to 20 jobs
                try:
                    title_elem = card.find('a', class_='title')
                    company_elem = card.find('a', class_='subTitle')
                    location_elem = card.find('li', class_='location')
                    salary_elem = card.find('li', class_='salary')
                    
                    if not (title_elem and company_elem):
                        continue
                    
                    job_url = title_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.naukri.com{job_url}"
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True),
                        'url': job_url.split('?')[0],
                        'location': location_elem.get_text(strip=True) if location_elem else 'India',
                        'salary': salary_elem.get_text(strip=True) if salary_elem else '',
                        'site': site,
                        'description': ''
                    }
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error scraping {site}: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_foundit(self, query: str) -> List[Dict]:
        """Scrape Foundit (Monster India)"""
        from urllib.parse import quote_plus
        
        jobs = []
        site = "Foundit"
        location = self.config.get('search', {}).get('default_location', 'India')
        
        query_encoded = quote_plus(query)
        url = f"https://www.foundit.in/srp/results?query={query_encoded}"
        if location:
            url += f"&locations={quote_plus(location)}"
        
        logger.info(f"Scraping {site} for: {query}")
        
        html = await self.fetch_with_retry(url, site)
        if not html:
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Try multiple selectors
            job_cards = soup.find_all('div', class_='jobTuple') or \
                       soup.find_all('article', class_='job-card') or \
                       soup.find_all('div', attrs={'data-job-id': True})
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('h3') or card.find('a', class_='job-title')
                    company_elem = card.find('div', class_='company-name') or card.find('span', class_='company')
                    location_elem = card.find('div', class_='location') or card.find('span', class_='loc')
                    salary_elem = card.find('span', class_='salary')
                    link_elem = title_elem.find('a') if title_elem else card.find('a')
                    
                    if not (title_elem and link_elem):
                        continue
                    
                    job_url = link_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.foundit.in{job_url}"
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True) if company_elem else 'Not specified',
                        'url': job_url.split('?')[0],
                        'location': location_elem.get_text(strip=True) if location_elem else 'India',
                        'salary': salary_elem.get_text(strip=True) if salary_elem else '',
                        'site': site,
                        'description': ''
                    }
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error scraping {site}: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_shine(self, query: str) -> List[Dict]:
        """Scrape Shine.com"""
        from urllib.parse import quote_plus
        
        jobs = []
        site = "Shine"
        
        query_encoded = quote_plus(query)
        url = f"https://www.shine.com/job-search/{query_encoded}-jobs"
        
        logger.info(f"Scraping {site} for: {query}")
        
        html = await self.fetch_with_retry(url, site)
        if not html:
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            job_cards = soup.find_all('li', id=lambda x: x and x.startswith('id_')) or \
                       soup.find_all('div', class_='jobCard')
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('a', class_='jobTitle') or card.find('h2', class_='title')
                    company_elem = card.find('div', class_='recruiterName') or card.find('span', class_='company')
                    location_elem = card.find('div', class_='location') or card.find('span', class_='loc')
                    salary_elem = card.find('div', class_='salary') or card.find('span', class_='package')
                    link_elem = title_elem if title_elem and title_elem.name == 'a' else title_elem.find('a') if title_elem else None
                    
                    if not (title_elem and link_elem):
                        continue
                    
                    job_url = link_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.shine.com{job_url}"
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True) if company_elem else 'Not specified',
                        'url': job_url.split('?')[0],
                        'location': location_elem.get_text(strip=True) if location_elem else 'India',
                        'salary': salary_elem.get_text(strip=True) if salary_elem else '',
                        'site': site,
                        'description': ''
                    }
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error scraping {site}: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_timesjobs(self, query: str) -> List[Dict]:
        """Scrape TimesJobs"""
        from urllib.parse import quote_plus
        
        jobs = []
        site = "TimesJobs"
        location = self.config.get('search', {}).get('default_location', 'India')
        
        query_encoded = quote_plus(query)
        url = f"https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords={query_encoded}"
        if location:
            url += f"&txtLocation={quote_plus(location)}"
        
        logger.info(f"Scraping {site} for: {query}")
        
        html = await self.fetch_with_retry(url, site)
        if not html:
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            job_cards = soup.find_all('li', class_='clearfix') or \
                       soup.find_all('article', class_='job')
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('h2')
                    if title_elem:
                        link_elem = title_elem.find('a')
                    else:
                        link_elem = card.find('a', class_='job-title')
                    
                    company_elem = card.find('h3', class_='joblist-comp-name') or card.find('span', class_='company')
                    location_elem = card.find('span', class_='loc') or card.find('div', class_='location')
                    salary_elem = card.find('span', class_='salary')
                    
                    if not (title_elem or link_elem):
                        continue
                    
                    job_url = link_elem.get('href', '') if link_elem else ''
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.timesjobs.com{job_url}"
                    
                    title = (title_elem or link_elem).get_text(strip=True)
                    
                    job = {
                        'title': title,
                        'company': company_elem.get_text(strip=True) if company_elem else 'Not specified',
                        'url': job_url.split('?')[0],
                        'location': location_elem.get_text(strip=True) if location_elem else 'India',
                        'salary': salary_elem.get_text(strip=True) if salary_elem else '',
                        'site': site,
                        'description': ''
                    }
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error scraping {site}: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_instahyre(self, query: str) -> List[Dict]:
        """Scrape Instahyre - Tech jobs in India"""
        from urllib.parse import quote_plus
        
        jobs = []
        site = "Instahyre"
        
        query_encoded = quote_plus(query)
        url = f"https://www.instahyre.com/search-jobs/?q={query_encoded}"
        
        logger.info(f"Scraping {site} for: {query}")
        
        html = await self.fetch_with_retry(url, site)
        if not html:
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            job_cards = soup.find_all('div', class_='opportunity-container') or \
                       soup.find_all('div', attrs={'data-opportunity-id': True})
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('div', class_='opportunity-title') or card.find('h3', class_='job-title')
                    company_elem = card.find('div', class_='company-name') or card.find('span', class_='company')
                    location_elem = card.find('div', class_='opportunity-location') or card.find('span', class_='location')
                    salary_elem = card.find('div', class_='salary-text') or card.find('span', class_='salary')
                    link_elem = card.find('a', class_='opportunity-link') or card.find('a')
                    
                    if not (title_elem and link_elem):
                        continue
                    
                    job_url = link_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.instahyre.com{job_url}"
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True) if company_elem else 'Not specified',
                        'url': job_url.split('?')[0],
                        'location': location_elem.get_text(strip=True) if location_elem else 'India',
                        'salary': salary_elem.get_text(strip=True) if salary_elem else '',
                        'site': site,
                        'description': ''
                    }
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error scraping {site}: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_cutshort(self, query: str) -> List[Dict]:
        """Scrape Cutshort - Startup & tech jobs in India"""
        from urllib.parse import quote_plus
        
        jobs = []
        site = "Cutshort"
        
        query_encoded = quote_plus(query)
        url = f"https://cutshort.io/job-search?q={query_encoded}&l=India"
        
        logger.info(f"Scraping {site} for: {query}")
        
        html = await self.fetch_with_retry(url, site)
        if not html:
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            job_cards = soup.find_all('div', class_='job-card') or \
                       soup.find_all('article', attrs={'data-job-id': True})
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('h3', class_='job-title') or card.find('a', class_='title')
                    company_elem = card.find('div', class_='company-name') or card.find('span', class_='company')
                    location_elem = card.find('span', class_='location') or card.find('div', class_='loc')
                    salary_elem = card.find('span', class_='salary-range') or card.find('div', class_='salary')
                    link_elem = card.find('a', class_='job-link') or card.find('a')
                    
                    if not (title_elem and link_elem):
                        continue
                    
                    job_url = link_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://cutshort.io{job_url}"
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True) if company_elem else 'Not specified',
                        'url': job_url.split('?')[0],
                        'location': location_elem.get_text(strip=True) if location_elem else 'India',
                        'salary': salary_elem.get_text(strip=True) if salary_elem else '',
                        'site': site,
                        'description': ''
                    }
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error scraping {site}: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_hirist(self, query: str) -> List[Dict]:
        """Scrape Hirist - IT jobs in India"""
        from urllib.parse import quote_plus
        
        jobs = []
        site = "Hirist"
        
        query_encoded = quote_plus(query)
        url = f"https://www.hirist.com/jobs/{query_encoded}-jobs"
        
        logger.info(f"Scraping {site} for: {query}")
        
        html = await self.fetch_with_retry(url, site)
        if not html:
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            job_cards = soup.find_all('div', class_='new-job-box') or \
                       soup.find_all('div', class_='card-body')
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('h3', class_='designation') or card.find('a', class_='title')
                    company_elem = card.find('div', class_='company-name') or card.find('span', class_='company')
                    location_elem = card.find('div', class_='loc') or card.find('span', class_='location')
                    salary_elem = card.find('div', class_='sal')
                    link_elem = title_elem.find('a') if title_elem else card.find('a')
                    
                    if not (title_elem and link_elem):
                        continue
                    
                    job_url = link_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.hirist.com{job_url}"
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True) if company_elem else 'Not specified',
                        'url': job_url.split('?')[0],
                        'location': location_elem.get_text(strip=True) if location_elem else 'India',
                        'salary': salary_elem.get_text(strip=True) if salary_elem else '',
                        'site': site,
                        'description': ''
                    }
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error scraping {site}: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_iimjobs(self, query: str) -> List[Dict]:
        """Scrape IIMJobs - Premium Indian job site"""
        from urllib.parse import quote_plus
        
        jobs = []
        site = "IIMJobs"
        
        query_encoded = quote_plus(query)
        url = f"https://www.iimjobs.com/j/{query_encoded}.html"
        
        logger.info(f"Scraping {site} for: {query}")
        
        html = await self.fetch_with_retry(url, site)
        if not html:
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            job_cards = soup.find_all('div', class_='job-box') or \
                       soup.find_all('div', class_='job-tile')
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('h3') or card.find('a', class_='title')
                    company_elem = card.find('div', class_='company') or card.find('span', class_='org')
                    location_elem = card.find('span', class_='loc')
                    salary_elem = card.find('span', class_='ctc')
                    link_elem = title_elem.find('a') if title_elem else card.find('a')
                    
                    if not (title_elem and link_elem):
                        continue
                    
                    job_url = link_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.iimjobs.com{job_url}"
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True) if company_elem else 'Not specified',
                        'url': job_url.split('?')[0],
                        'location': location_elem.get_text(strip=True) if location_elem else 'India',
                        'salary': salary_elem.get_text(strip=True) if salary_elem else '',
                        'site': site,
                        'description': ''
                    }
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error scraping {site}: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_freshersworld(self, query: str) -> List[Dict]:
        """Scrape Freshersworld - Entry-level jobs in India"""
        from urllib.parse import quote_plus
        
        jobs = []
        site = "Freshersworld"
        
        query_encoded = quote_plus(query)
        url = f"https://www.freshersworld.com/jobs/jobsearch/{query_encoded}-jobs"
        
        logger.info(f"Scraping {site} for: {query}")
        
        html = await self.fetch_with_retry(url, site)
        if not html:
            return jobs
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            job_cards = soup.find_all('div', class_='job-container') or \
                       soup.find_all('div', class_='job-box')
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('h3', class_='latest-jobs-title') or card.find('span', class_='wrap-title')
                    company_elem = card.find('h3', class_='latest-jobs-company') or card.find('span', class_='company')
                    location_elem = card.find('span', class_='job-location')
                    link_elem = title_elem.find('a') if title_elem else card.find('a')
                    
                    if not (title_elem and link_elem):
                        continue
                    
                    job_url = link_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.freshersworld.com{job_url}"
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True) if company_elem else 'Not specified',
                        'url': job_url.split('?')[0],
                        'location': location_elem.get_text(strip=True) if location_elem else 'India',
                        'salary': '',
                        'site': site,
                        'description': ''
                    }
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing {site} job: {e}")
                    continue
            
            self.stats.record_scraped(site, len(jobs))
            logger.info(f"Scraped {len(jobs)} jobs from {site}")
            
        except Exception as e:
            logger.error(f"Error scraping {site}: {e}")
            self.stats.record_error(site)
        
        return jobs
    
    async def scrape_all_sites(self, queries: List[str]) -> List[Dict]:
        """Scrape multiple job sites concurrently"""
        all_jobs = []
        
        # Enhance queries with AI if available
        if self.job_discovery and len(queries) > 0:
            try:
                logger.info(f"🤖 Using AI to generate additional search variations...")
                ai_queries = await self.job_discovery.generate_search_queries(queries[0])
                
                # Combine and deduplicate queries
                all_queries = queries + ai_queries
                
                # Normalize and deduplicate (case-insensitive, remove duplicates)
                unique_queries = []
                seen_normalized = set()
                for q in all_queries:
                    normalized = q.lower().strip()
                    if normalized not in seen_normalized:
                        unique_queries.append(q)
                        seen_normalized.add(normalized)
                
                # Limit to reasonable number to avoid duplicate job flood
                queries = unique_queries[:8]  # Reduced from 15 to 8 to minimize duplicates
                logger.info(f"✨ Enhanced search with {len(queries)} unique query variations")
            except Exception as e:
                logger.warning(f"Could not enhance queries with AI: {e}")
        
        # Initialize stealth browser if enabled
        if self.use_stealth and STEALTH_AVAILABLE and not self.stealth_scraper:
            logger.info("Initializing stealth browser mode...")
            self.stealth_scraper = StealthBrowserScraper()
            await self.stealth_scraper.init_browser(headless=True)
        
        # Get enabled sites from config
        enabled_sites = self.config.get('sites', {})
        
        # Create tasks for concurrent scraping
        tasks = []
        for query in queries:
            if enabled_sites.get('linkedin', {}).get('enabled', False):
                tasks.append(self.scrape_linkedin(query))
            
            if enabled_sites.get('linkedin_posts', {}).get('enabled', False):
                tasks.append(self.scrape_linkedin_posts(query))
            
            if enabled_sites.get('glassdoor', {}).get('enabled', False):
                if self.use_stealth and STEALTH_AVAILABLE:
                    tasks.append(self.scrape_glassdoor_stealth(query))
                else:
                    tasks.append(self.scrape_glassdoor(query))
            
            if enabled_sites.get('google_jobs', {}).get('enabled', False):
                if self.use_stealth and STEALTH_AVAILABLE:
                    tasks.append(self.scrape_google_jobs_stealth(query))
                else:
                    tasks.append(self.scrape_google_jobs(query))
            
            if enabled_sites.get('indeed', {}).get('enabled', False):
                if self.use_stealth and STEALTH_AVAILABLE:
                    tasks.append(self.scrape_indeed_stealth(query))
                else:
                    tasks.append(self.scrape_indeed(query))
            
            if enabled_sites.get('bing_jobs', {}).get('enabled', False):
                tasks.append(self.scrape_bing_jobs(query))
            
            if enabled_sites.get('remotive', {}).get('enabled', False):
                tasks.append(self.scrape_remotive(query))
            
            # Indian Job Sites
            if enabled_sites.get('naukri', {}).get('enabled', False):
                tasks.append(self.scrape_naukri(query))
            
            if enabled_sites.get('foundit', {}).get('enabled', False):
                tasks.append(self.scrape_foundit(query))
            
            if enabled_sites.get('shine', {}).get('enabled', False):
                tasks.append(self.scrape_shine(query))
            
            if enabled_sites.get('timesjobs', {}).get('enabled', False):
                tasks.append(self.scrape_timesjobs(query))
            
            if enabled_sites.get('instahyre', {}).get('enabled', False):
                tasks.append(self.scrape_instahyre(query))
            
            if enabled_sites.get('cutshort', {}).get('enabled', False):
                tasks.append(self.scrape_cutshort(query))
            
            if enabled_sites.get('hirist', {}).get('enabled', False):
                tasks.append(self.scrape_hirist(query))
            
            if enabled_sites.get('iimjobs', {}).get('enabled', False):
                tasks.append(self.scrape_iimjobs(query))
            
            if enabled_sites.get('freshersworld', {}).get('enabled', False):
                tasks.append(self.scrape_freshersworld(query))
        
        if not tasks:
            logger.warning("No sites enabled for scraping!")
            return all_jobs
        
        # Run all scrapers concurrently
        logger.info(f"Running {len(tasks)} scraping tasks concurrently...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraping task failed: {result}")
        
        return all_jobs
    
    async def process_jobs(self, jobs: List[Dict]):
        """Process scraped jobs, filter, and send new ones to Telegram"""
        new_jobs_count = 0
        site_job_counts = {}  # Track jobs per site for reporting
        processed_jobs = []  # Store processed jobs for similarity checking
        
        # Group jobs by site for better distribution
        jobs_by_site = {}
        for job in jobs:
            site = job['site']
            if site not in jobs_by_site:
                jobs_by_site[site] = []
            jobs_by_site[site].append(job)
        
        logger.info(f"📊 Raw job counts by site: {', '.join([f'{site}: {len(jobs_by_site[site])}' for site in jobs_by_site])}")
        
        # Process jobs in round-robin fashion from each site for better distribution
        # This prevents one site from flooding notifications before others get a chance
        max_iterations = max(len(site_jobs) for site_jobs in jobs_by_site.values()) if jobs_by_site else 0
        
        for i in range(max_iterations):
            for site in sorted(jobs_by_site.keys()):  # Sort for consistent ordering
                site_jobs = jobs_by_site[site]
                if i >= len(site_jobs):
                    continue
                
                job = site_jobs[i]
                
                # Apply filters
                if not self.job_filter.matches(job):
                    self.stats.record_filtered()
                    continue
                
                # Check for duplicates by hash
                job_hash = self._hash_job(job)
                
                if job_hash in self.seen_jobs:
                    self.stats.record_duplicate()
                    continue
                
                # Check for similar jobs (catch duplicates with slightly different titles/URLs)
                is_similar = False
                for processed_job in processed_jobs[-100:]:  # Check last 100 jobs
                    if self._is_similar_job(job, processed_job):
                        logger.debug(f"Similar job found: {job['title']} at {job['company']}")
                        self.stats.record_duplicate()
                        is_similar = True
                        break
                
                if is_similar:
                    continue
                
                # New job found!
                self.seen_jobs.add(job_hash)
                self._save_job(job, job_hash)
                self.stats.record_new(job['site'])
                processed_jobs.append(job)
                
                # Track for reporting
                if site not in site_job_counts:
                    site_job_counts[site] = 0
                site_job_counts[site] += 1
                
                # Send to Telegram
                await self.send_telegram_message(job)
                new_jobs_count += 1
                
                # Rate limit to avoid Telegram flooding (max 30 msgs/second)
                await asyncio.sleep(0.5)
        
        if new_jobs_count > 0:
            logger.info(f"✅ [NEW] Found {new_jobs_count} new jobs")
            logger.info(f"📊 [DISTRIBUTION] Jobs sent per site: {', '.join([f'{site}: {count}' for site, count in sorted(site_job_counts.items())])}")
        else:
            logger.info("No new jobs found this cycle")
        
        return new_jobs_count
    
    async def run_scraping_cycle(self, queries: List[str]):
        """Run one complete scraping cycle"""
        logger.info("=" * 60)
        logger.info("Starting scraping cycle...")
        start_time = time.time()
        
        try:
            # Scrape all sites
            jobs = await self.scrape_all_sites(queries)
            
            # Process and filter jobs
            new_jobs = await self.process_jobs(jobs)
            
            # Update stats
            self.stats.record_cycle()
            self.last_successful_scrape = datetime.now()
            
            elapsed = time.time() - start_time
            logger.info(f"[OK] Cycle completed in {elapsed:.2f} seconds")
            logger.info(f"Jobs: {len(jobs)} scraped, {new_jobs} new")
            
        except Exception as e:
            logger.error(f"[ERROR] Cycle failed: {e}", exc_info=True)
            self.stats.record_error()
            self.consecutive_failures += 1
            
            if self.consecutive_failures >= self.max_consecutive_failures:
                await self.send_alert(
                    f"🚨 CRITICAL: Scraper has failed {self.consecutive_failures} times!\n"
                    f"Last error: {str(e)}"
                )
    
    async def health_check(self):
        """Perform health check and send alerts if needed"""
        now = datetime.now()
        time_since_success = now - self.last_successful_scrape
        
        # Alert if no successful scrape in 1 hour
        if time_since_success > timedelta(hours=1):
            await self.send_alert(
                f"⚠️ Health Check Failed!\n"
                f"No successful scrape in {time_since_success}\n"
                f"Consecutive failures: {self.consecutive_failures}"
            )
    
    async def periodic_stats(self, interval_hours: int = 24):
        """Send periodic statistics summary"""
        while True:
            await asyncio.sleep(interval_hours * 3600)
            await self.send_stats_summary()
            
            # Reset stats after sending
            if self.config.get('monitoring', {}).get('reset_stats_after_summary', False):
                self.stats.reset()
    
    async def periodic_health_check(self, interval_minutes: int = 30):
        """Perform periodic health checks"""
        while True:
            await asyncio.sleep(interval_minutes * 60)
            await self.health_check()
    
    async def start(self):
        """Start the 24/7 scraping bot"""
        queries = self.config.get('search', {}).get('queries', [])
        interval = self.config.get('scraping', {}).get('interval', 300)  # Default 5 minutes
        
        if not queries:
            logger.error("No search queries configured!")
            return
        
        # Create persistent aiohttp session for connection pooling
        timeout = aiohttp.ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(
            limit=self.config.get('scraping', {}).get('connection_pool_size', 10),
            limit_per_host=5
        )
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={'User-Agent': UserAgentRotator.get_random()}
        )
        
        logger.info("=" * 60)
        logger.info("🚀 Starting Job Scraper Bot")
        logger.info(f"📊 Monitoring {len(queries)} queries")
        logger.info(f"⏱ Scraping interval: {interval} seconds")
        logger.info(f"🌐 Enabled sites: {[k for k, v in self.config.get('sites', {}).items() if v.get('enabled')]}")
        logger.info("=" * 60)
        
        # Send startup notification
        await self.send_alert(
            f"🤖 Job Scraper Bot Started!\n"
            f"Queries: {', '.join(queries)}\n"
            f"Interval: {interval}s"
        )
        
        try:
            # Start background tasks
            stats_interval = self.config.get('monitoring', {}).get('stats_interval_hours', 24)
            health_interval = self.config.get('monitoring', {}).get('health_check_interval_minutes', 30)
            
            asyncio.create_task(self.periodic_stats(stats_interval))
            asyncio.create_task(self.periodic_health_check(health_interval))
            
            # Main scraping loop
            while True:
                await self.run_scraping_cycle(queries)
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("\n⏹ Shutting down gracefully...")
            await self.send_alert("⏹ Job Scraper Bot Stopped")
        except Exception as e:
            logger.critical(f"💥 Fatal error: {e}", exc_info=True)
            await self.send_alert(f"💥 FATAL ERROR: {str(e)}\nBot crashed!")
        finally:
            # Cleanup stealth browser
            if self.stealth_scraper:
                try:
                    await self.stealth_scraper.close()
                    logger.info("Stealth browser closed")
                except Exception as e:
                    logger.error(f"Error closing stealth browser: {e}")
            
            if self.session:
                await self.session.close()
            logger.info("✅ Cleanup complete")


# ========== MAIN ENTRY POINT ==========

async def main():
    """Main entry point"""
    config_path = Path('config.yaml')
    
    if not config_path.exists():
        logger.error("config.yaml not found! Please create configuration file.")
        logger.info("See config.example.yaml for reference")
        return
    
    # Load configuration
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Validate required config
    if not config.get('telegram', {}).get('bot_token'):
        logger.error("Telegram bot token not configured!")
        return
    
    if not config.get('telegram', {}).get('chat_id'):
        logger.error("Telegram chat ID not configured!")
        return
    
    # Initialize and start scraper
    scraper = JobScraper(config)
    await scraper.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

