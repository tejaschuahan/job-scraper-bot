"""
Advanced anti-bot bypass scrapers using Playwright
These use real browser instances with stealth techniques
"""
import asyncio
import random
import logging
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class StealthBrowserScraper:
    """Browser-based scraper with anti-detection measures"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.ua = UserAgent()
        
    async def init_browser(self, headless: bool = True):
        """Initialize browser with stealth settings"""
        self.playwright = await async_playwright().start()
        
        # Launch browser with stealth options
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-gpu'
            ]
        )
        
    async def close_browser(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def create_stealth_page(self) -> Page:
        """Create a new page with anti-detection scripts"""
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=self.ua.random,
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # New York
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        
        page = await context.new_page()
        
        # Inject anti-detection scripts
        await page.add_init_script("""
            // Override the navigator.webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override the plugins property
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Override the languages property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Override chrome property
            window.chrome = {
                runtime: {}
            };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        return page
    
    async def human_like_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """Add human-like random delay"""
        delay = random.uniform(min_ms / 1000, max_ms / 1000)
        await asyncio.sleep(delay)
    
    async def human_scroll(self, page: Page):
        """Simulate human scrolling behavior"""
        # Scroll down gradually
        for _ in range(random.randint(2, 4)):
            await page.evaluate('window.scrollBy(0, window.innerHeight / 2)')
            await self.human_like_delay(300, 800)
        
        # Scroll back up a bit
        await page.evaluate('window.scrollBy(0, -window.innerHeight / 4)')
        await self.human_like_delay(200, 500)
    
    async def scrape_indeed_stealth(self, query: str, location: str = "") -> List[Dict]:
        """
        Scrape Indeed using real browser with anti-detection
        """
        jobs = []
        
        try:
            page = await self.create_stealth_page()
            
            # Build URL
            query_encoded = query.replace(' ', '+')
            location_encoded = location.replace(' ', '+') if location else ''
            url = f"https://www.indeed.com/jobs?q={query_encoded}"
            if location_encoded:
                url += f"&l={location_encoded}"
            url += "&fromage=1&sort=date"
            
            logger.info(f"Loading Indeed with stealth browser: {url}")
            
            # Navigate with realistic behavior
            await page.goto(url, wait_until='load', timeout=60000)
            await self.human_like_delay(2000, 3000)
            
            # Scroll like a human
            await self.human_scroll(page)
            
            # Wait for job cards to load - try multiple selectors
            try:
                await page.wait_for_selector('div.job_seen_beacon, td.resultContent, div.jobsearch-ResultsList, div[data-testid="jobsearch-results"]', timeout=15000)
                logger.info("Indeed job cards loaded successfully")
            except:
                logger.warning("Job cards not found on Indeed - site may have changed structure")
            
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Parse jobs
            job_cards = soup.find_all('div', class_='job_seen_beacon') or \
                       soup.find_all('td', class_='resultContent')
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('h2', class_='jobTitle') or \
                                card.find('a', class_='jcs-JobTitle')
                    
                    company_elem = card.find('span', class_='companyName')
                    location_elem = card.find('div', class_='companyLocation')
                    salary_elem = card.find('div', class_='salary-snippet')
                    link_elem = card.find('a', class_='jcs-JobTitle') or \
                               (title_elem.find('a') if title_elem else None)
                    
                    if not (title_elem and company_elem and link_elem):
                        continue
                    
                    job_url = link_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.indeed.com{job_url}"
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True),
                        'url': job_url.split('?')[0],
                        'location': location_elem.get_text(strip=True) if location_elem else '',
                        'salary': salary_elem.get_text(strip=True) if salary_elem else '',
                        'site': 'Indeed',
                        'description': ''
                    }
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing Indeed job: {e}")
                    continue
            
            logger.info(f"Scraped {len(jobs)} jobs from Indeed (stealth)")
            await page.close()
            
        except Exception as e:
            logger.error(f"Error in Indeed stealth scraper: {e}")
        
        return jobs
    
    async def scrape_glassdoor_stealth(self, query: str, location: str = "") -> List[Dict]:
        """
        Scrape Glassdoor using real browser with anti-detection
        """
        jobs = []
        
        try:
            page = await self.create_stealth_page()
            
            # Build URL
            from urllib.parse import quote_plus
            query_encoded = quote_plus(query)
            location_encoded = quote_plus(location) if location else ''
            
            url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query_encoded}"
            if location_encoded:
                url += f"&locT=C&locId=1&locKeyword={location_encoded}"
            
            logger.info(f"Loading Glassdoor with stealth browser: {url}")
            
            # Navigate with longer timeout for Cloudflare check
            await page.goto(url, wait_until='load', timeout=60000)
            await self.human_like_delay(3000, 5000)  # Wait for Cloudflare
            
            # Handle potential popups
            try:
                close_button = page.locator('button[class*="CloseButton"]')
                if await close_button.count() > 0:
                    await close_button.first.click()
                    await self.human_like_delay(500, 1000)
            except:
                pass
            
            # Scroll like human
            await self.human_scroll(page)
            
            # Wait for jobs
            try:
                await page.wait_for_selector('li.react-job-listing, article[data-test="jobListing"]', timeout=10000)
            except:
                logger.warning("Job listings not found on Glassdoor")
            
            # Get content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Parse jobs
            job_cards = soup.find_all('li', class_='react-job-listing') or \
                       soup.find_all('article', attrs={'data-test': 'jobListing'})
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('a', attrs={'data-test': 'job-link'}) or \
                                card.find('a', class_='job-title')
                    
                    company_elem = card.find('div', attrs={'data-test': 'employer-name'}) or \
                                  card.find('div', class_='employer-name')
                    
                    location_elem = card.find('div', attrs={'data-test': 'emp-location'}) or \
                                   card.find('span', class_='loc')
                    
                    salary_elem = card.find('span', attrs={'data-test': 'detailSalary'})
                    
                    if not (title_elem and company_elem):
                        continue
                    
                    job_url = title_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.glassdoor.com{job_url}"
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True),
                        'url': job_url.split('?')[0],
                        'location': location_elem.get_text(strip=True) if location_elem else '',
                        'salary': salary_elem.get_text(strip=True) if salary_elem else '',
                        'site': 'Glassdoor',
                        'description': ''
                    }
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing Glassdoor job: {e}")
                    continue
            
            logger.info(f"Scraped {len(jobs)} jobs from Glassdoor (stealth)")
            await page.close()
            
        except Exception as e:
            logger.error(f"Error in Glassdoor stealth scraper: {e}")
        
        return jobs
    
    async def scrape_google_jobs_stealth(self, query: str, location: str = "") -> List[Dict]:
        """
        Scrape Google Jobs using real browser with anti-detection
        """
        jobs = []
        
        try:
            page = await self.create_stealth_page()
            
            # Build search query
            from urllib.parse import quote_plus
            search_query = f"{query} jobs"
            if location:
                search_query += f" {location}"
            
            url = f"https://www.google.com/search?q={quote_plus(search_query)}&ibp=htl;jobs"
            
            logger.info(f"Loading Google Jobs with stealth browser")
            
            # Navigate
            await page.goto(url, wait_until='load', timeout=60000)
            await self.human_like_delay(3000, 5000)
            
            # Scroll to load jobs
            await self.human_scroll(page)
            
            # Wait for job cards - try multiple selectors
            try:
                await page.wait_for_selector('div.PwjeAc, li.iFjolb, div.job-card, div[data-job-id]', timeout=15000)
                logger.info("Google Jobs cards loaded successfully")
            except:
                logger.warning("Job cards not found on Google Jobs - site may have changed structure")
            
            # Get content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Parse jobs
            job_cards = soup.find_all('div', class_='PwjeAc') or \
                       soup.find_all('li', class_='iFjolb')
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find('div', class_='BjJfJf') or \
                                card.find('h2', class_='KLsYvd')
                    
                    company_elem = card.find('div', class_='vNEEBe')
                    location_elem = card.find('div', class_='Qk80Jf')
                    
                    link_elem = card.find('a')
                    
                    if not (title_elem and company_elem):
                        continue
                    
                    job_url = ''
                    if link_elem and link_elem.get('href'):
                        job_url = link_elem['href']
                        if job_url.startswith('/url?q='):
                            job_url = job_url.split('/url?q=')[1].split('&')[0]
                    
                    job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True),
                        'url': job_url or f"https://www.google.com/search?q={quote_plus(search_query)}&ibp=htl;jobs",
                        'location': location_elem.get_text(strip=True) if location_elem else '',
                        'salary': '',
                        'site': 'Google Jobs',
                        'description': ''
                    }
                    jobs.append(job)
                    
                except Exception as e:
                    logger.debug(f"Error parsing Google job: {e}")
                    continue
            
            logger.info(f"Scraped {len(jobs)} jobs from Google Jobs (stealth)")
            await page.close()
            
        except Exception as e:
            logger.error(f"Error in Google Jobs stealth scraper: {e}")
        
        return jobs
