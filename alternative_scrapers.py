"""
Alternative job scrapers using APIs and RSS feeds
These are more reliable than HTML scraping
"""
import aiohttp
import asyncio
from typing import List, Dict
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


async def scrape_remotive(query: str, session: aiohttp.ClientSession) -> List[Dict]:
    """
    Scrape Remotive.io API (free, no rate limits for reasonable use)
    Focuses on remote jobs
    """
    jobs = []
    url = "https://remotive.com/api/remote-jobs"
    
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status == 200:
                data = await response.json()
                
                for job_data in data.get('jobs', []):
                    # Filter by query
                    title = job_data.get('title', '').lower()
                    description = job_data.get('description', '').lower()
                    query_lower = query.lower()
                    
                    if query_lower in title or query_lower in description:
                        job = {
                            'title': job_data.get('title', ''),
                            'company': job_data.get('company_name', ''),
                            'url': job_data.get('url', ''),
                            'location': 'Remote',
                            'salary': '',
                            'job_type': job_data.get('job_type', ''),
                            'description': job_data.get('description', '')[:500],
                            'site': 'Remotive'
                        }
                        jobs.append(job)
                
                logger.info(f"Scraped {len(jobs)} jobs from Remotive")
    except Exception as e:
        logger.error(f"Error scraping Remotive: {e}")
    
    return jobs


async def scrape_adzuna(query: str, app_id: str, app_key: str, session: aiohttp.ClientSession) -> List[Dict]:
    """
    Scrape Adzuna API (requires free API key from https://developer.adzuna.com/)
    Aggregates from many sources
    """
    jobs = []
    
    if not app_id or not app_key:
        logger.warning("Adzuna API credentials not configured")
        return jobs
    
    url = f"https://api.adzuna.com/v1/api/jobs/us/search/1"
    params = {
        'app_id': app_id,
        'app_key': app_key,
        'results_per_page': 50,
        'what': query,
        'sort_by': 'date'
    }
    
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status == 200:
                data = await response.json()
                
                for job_data in data.get('results', []):
                    job = {
                        'title': job_data.get('title', ''),
                        'company': job_data.get('company', {}).get('display_name', ''),
                        'url': job_data.get('redirect_url', ''),
                        'location': job_data.get('location', {}).get('display_name', ''),
                        'salary': f"${job_data.get('salary_min', 0)}-${job_data.get('salary_max', 0)}" if job_data.get('salary_min') else '',
                        'job_type': job_data.get('contract_type', ''),
                        'description': job_data.get('description', '')[:500],
                        'site': 'Adzuna'
                    }
                    jobs.append(job)
                
                logger.info(f"Scraped {len(jobs)} jobs from Adzuna")
    except Exception as e:
        logger.error(f"Error scraping Adzuna: {e}")
    
    return jobs


async def scrape_github_jobs(query: str, session: aiohttp.ClientSession) -> List[Dict]:
    """
    Scrape GitHub Jobs RSS feed (tech jobs)
    """
    jobs = []
    
    # Note: GitHub Jobs was shut down in 2021, but keeping this as template
    # You can replace with other RSS feeds
    
    return jobs


async def scrape_usajobs(query: str, session: aiohttp.ClientSession) -> List[Dict]:
    """
    Scrape USAJobs API (US government jobs, free API)
    """
    jobs = []
    url = "https://data.usajobs.gov/api/search"
    
    headers = {
        'Host': 'data.usajobs.gov',
        'User-Agent': 'your-email@example.com',  # USAJobs requires email in UA
        'Authorization-Key': 'YOUR_API_KEY'  # Get free key from https://developer.usajobs.gov/
    }
    
    params = {
        'Keyword': query,
        'ResultsPerPage': 500
    }
    
    try:
        async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status == 200:
                data = await response.json()
                
                for job_data in data.get('SearchResult', {}).get('SearchResultItems', []):
                    match_data = job_data.get('MatchedObjectDescriptor', {})
                    
                    job = {
                        'title': match_data.get('PositionTitle', ''),
                        'company': match_data.get('OrganizationName', 'US Government'),
                        'url': match_data.get('PositionURI', ''),
                        'location': ', '.join([loc.get('LocationName', '') for loc in match_data.get('PositionLocation', [])]),
                        'salary': f"${match_data.get('PositionRemuneration', [{}])[0].get('MinimumRange', '')}-${match_data.get('PositionRemuneration', [{}])[0].get('MaximumRange', '')}",
                        'job_type': match_data.get('PositionSchedule', [{}])[0].get('Name', ''),
                        'description': match_data.get('PositionFormattedDescription', [{}])[0].get('Content', '')[:500],
                        'site': 'USAJobs'
                    }
                    jobs.append(job)
                
                logger.info(f"Scraped {len(jobs)} jobs from USAJobs")
    except Exception as e:
        logger.error(f"Error scraping USAJobs: {e}")
    
    return jobs


async def scrape_jobs2careers(query: str, api_key: str, session: aiohttp.ClientSession) -> List[Dict]:
    """
    Scrape Jobs2Careers API (paid API, aggregates multiple sources)
    """
    jobs = []
    
    if not api_key:
        logger.warning("Jobs2Careers API key not configured")
        return jobs
    
    url = "https://api.jobs2careers.com/api/search.php"
    params = {
        'id': api_key,
        'q': query,
        'l': '',
        'format': 'json'
    }
    
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status == 200:
                data = await response.json()
                
                for job_data in data:
                    job = {
                        'title': job_data.get('title', ''),
                        'company': job_data.get('company', ''),
                        'url': job_data.get('url', ''),
                        'location': job_data.get('location', ''),
                        'salary': '',
                        'job_type': '',
                        'description': job_data.get('description', '')[:500],
                        'site': 'Jobs2Careers'
                    }
                    jobs.append(job)
                
                logger.info(f"Scraped {len(jobs)} jobs from Jobs2Careers")
    except Exception as e:
        logger.error(f"Error scraping Jobs2Careers: {e}")
    
    return jobs


# Instructions for getting API keys:
"""
FREE APIs:
1. Remotive - No API key needed! Just works.
2. Adzuna - Free tier: https://developer.adzuna.com/ (10,000 calls/month)
3. USAJobs - Free: https://developer.usajobs.gov/ (government jobs)

PAID APIs (but more reliable than scraping):
4. Jobs2Careers - Paid API
5. Reed API (UK jobs) - https://www.reed.co.uk/developers
6. Careerjet API - https://www.careerjet.com/partners/api/

To use these, add to your config.yaml:

apis:
  adzuna:
    app_id: "YOUR_APP_ID"
    app_key: "YOUR_APP_KEY"
  usajobs:
    api_key: "YOUR_API_KEY"
    email: "your@email.com"
"""
