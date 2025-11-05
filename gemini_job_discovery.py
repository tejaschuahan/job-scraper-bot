"""
Gemini-Powered Job Discovery System
Uses AI to find job listings from various sources beyond traditional scrapers
"""

import google.generativeai as genai
import logging
from typing import List, Dict, Optional
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class GeminiJobDiscovery:
    def __init__(self, gemini_client):
        """Initialize with Gemini AI client"""
        self.gemini = gemini_client
        self.model = gemini_client.model
        logger.info("🔍 Gemini Job Discovery initialized")
    
    async def discover_job_boards(self, role: str, location: str = "India") -> List[Dict]:
        """
        Use Gemini to discover job boards and sources for a specific role
        
        Args:
            role: Job role to search for
            location: Location to search in
        
        Returns:
            List of job board URLs and search strategies
        """
        try:
            prompt = f"""
You are a job search expert. List the best job boards and websites to find "{role}" jobs in {location}.

For each source, provide:
1. Website name
2. Direct search URL (with query parameters filled)
3. Why this source is good for this role
4. Estimated number of listings

Focus on:
- Indian job portals (Naukri, Shine, TimesJobs, etc.)
- Tech job boards (AngelList, Wellfound, Instahyre, etc.)
- General sites (LinkedIn, Indeed)
- Niche/specialized boards for this role
- Company career pages (if relevant)

Return as JSON array:
[
  {{
    "name": "Website name",
    "url": "Direct search URL with query",
    "reason": "Why good for this role",
    "expected_count": "Low/Medium/High"
  }}
]

Provide 8-10 best sources.
"""
            
            response = self.model.generate_content(prompt)
            sources = json.loads(response.text.strip())
            logger.info(f"📍 Discovered {len(sources)} job sources for {role}")
            return sources
            
        except Exception as e:
            logger.error(f"Error discovering job boards: {e}")
            return []
    
    async def generate_search_queries(self, role: str) -> List[str]:
        """
        Generate comprehensive search query variations using Gemini
        
        Args:
            role: Base job role
        
        Returns:
            List of search query variations
        """
        try:
            prompt = f"""
Generate 8-10 DISTINCT and DIFFERENT job search queries for finding "{role}" positions in Delhi NCR, India.

IMPORTANT: 
- Make each query meaningfully different to avoid duplicate results
- PRIORITIZE Delhi, Gurgaon, Noida, New Delhi locations in queries
- Include "Delhi" or "NCR" in 60% of queries

Include:
- Exact role name with Delhi/NCR (2-3 queries)
- Most common synonym with location (1-2 queries)
- Seniority variations (2-3 queries: junior, associate, entry-level) with Delhi
- Related but different roles (1-2 queries)

Examples for "data analyst":
- data analyst delhi
- data analyst gurgaon noida
- business intelligence analyst ncr
- junior data analyst delhi
- entry level analyst delhi ncr
- BI analyst new delhi
- reporting analyst gurgaon

Return ONLY a JSON array of strings (8-10 queries max):
["query1", "query2", "query3", ...]

No explanations, no duplicates, just distinct queries with Delhi NCR focus.
"""
            
            response = self.model.generate_content(prompt)
            queries = json.loads(response.text.strip())
            logger.info(f"🔤 Generated {len(queries)} distinct search variations for {role}")
            return queries[:10]  # Limit to 10 max
            
        except Exception as e:
            logger.error(f"Error generating search queries: {e}")
            return [role]
    
    async def extract_jobs_from_text(self, text: str, source: str) -> List[Dict]:
        """
        Use Gemini to extract job listings from unstructured text
        
        Args:
            text: Raw text containing job information
            source: Source website/platform
        
        Returns:
            List of extracted job dictionaries
        """
        try:
            prompt = f"""
Extract all job listings from this text. Each job should include:
- title (job title)
- company (company name)
- location (city/location)
- url (application link if present, else null)
- description (brief summary)

Text from {source}:
{text[:3000]}

Return as JSON array:
[
  {{
    "title": "Job title",
    "company": "Company name",
    "location": "Location",
    "url": "URL or null",
    "description": "Brief description"
  }}
]

If no jobs found, return empty array [].
"""
            
            response = self.model.generate_content(prompt)
            jobs = json.loads(response.text.strip())
            logger.info(f"📋 Extracted {len(jobs)} jobs from {source}")
            
            # Add metadata
            for job in jobs:
                job['site'] = source
                job['scraped_at'] = datetime.now().isoformat()
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error extracting jobs from text: {e}")
            return []
    
    async def find_company_career_pages(self, role: str, location: str = "India") -> List[Dict]:
        """
        Find relevant company career pages for a role
        
        Args:
            role: Job role
            location: Location
        
        Returns:
            List of company career page URLs
        """
        try:
            prompt = f"""
List 15-20 companies in {location} that frequently hire for "{role}" positions.

Focus on:
- Major tech companies
- Startups known for this role
- Consulting firms
- Product companies

For each company provide:
- Company name
- Career page URL (actual URL format like: https://company.com/careers)
- Why they hire this role

Return as JSON:
[
  {{
    "company": "Company Name",
    "careers_url": "https://...",
    "reason": "Why relevant"
  }}
]
"""
            
            response = self.model.generate_content(prompt)
            companies = json.loads(response.text.strip())
            logger.info(f"🏢 Found {len(companies)} companies hiring {role}")
            return companies
            
        except Exception as e:
            logger.error(f"Error finding company career pages: {e}")
            return []
    
    async def suggest_networking_opportunities(self, role: str) -> List[Dict]:
        """
        Suggest LinkedIn groups, Slack communities, etc. where jobs are posted
        
        Args:
            role: Job role
        
        Returns:
            List of networking opportunities
        """
        try:
            prompt = f"""
List online communities, groups, and platforms where "{role}" jobs are frequently posted in India.

Include:
- LinkedIn groups
- Slack/Discord communities
- Telegram channels
- WhatsApp groups (if public)
- Reddit communities
- Facebook groups

For each provide:
- Platform name
- Group/Channel name
- How to join/access
- Activity level (High/Medium/Low)

Return as JSON:
[
  {{
    "platform": "Platform name",
    "name": "Group/Channel name",
    "access": "How to join",
    "activity": "High/Medium/Low"
  }}
]
"""
            
            response = self.model.generate_content(prompt)
            opportunities = json.loads(response.text.strip())
            logger.info(f"🌐 Found {len(opportunities)} networking opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error finding networking opportunities: {e}")
            return []
    
    async def analyze_job_market(self, role: str, location: str = "India") -> Dict:
        """
        Get market intelligence about a role
        
        Args:
            role: Job role
            location: Location
        
        Returns:
            Market analysis dictionary
        """
        try:
            prompt = f"""
Provide a brief market analysis for "{role}" positions in {location}.

Include:
1. Demand level (High/Medium/Low)
2. Average salary range (in LPA for India)
3. Top hiring cities
4. Top 5 skills in demand
5. Growth trend (Growing/Stable/Declining)
6. Best time to apply (if seasonal)

Return as JSON:
{{
  "demand": "High/Medium/Low",
  "salary_range": "X-Y LPA",
  "top_cities": ["City1", "City2", "City3"],
  "key_skills": ["Skill1", "Skill2", "Skill3", "Skill4", "Skill5"],
  "trend": "Growing/Stable/Declining",
  "best_season": "Description",
  "advice": "2-3 sentence job search tip"
}}
"""
            
            response = self.model.generate_content(prompt)
            analysis = json.loads(response.text.strip())
            logger.info(f"📊 Generated market analysis for {role}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing job market: {e}")
            return {}
    
    async def optimize_search_strategy(self, role: str, user_profile: Dict) -> Dict:
        """
        Create a personalized job search strategy
        
        Args:
            role: Target job role
            user_profile: User's skills, experience, preferences
        
        Returns:
            Search strategy recommendations
        """
        try:
            prompt = f"""
Create a personalized job search strategy for:

Target Role: {role}
User Experience: {user_profile.get('experience', 'Entry-level')}
User Skills: {', '.join(user_profile.get('skills', ['General']))}
Location Preference: {user_profile.get('location', 'Flexible')}

Provide:
1. Priority job boards (top 5)
2. Best keywords to search
3. Companies to target directly
4. Skills to highlight
5. Red flags to avoid
6. Application tips

Return as JSON:
{{
  "priority_boards": ["Board1", "Board2", "Board3", "Board4", "Board5"],
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "target_companies": ["Company1", "Company2", "Company3"],
  "highlight_skills": ["Skill1", "Skill2", "Skill3"],
  "avoid_flags": ["Flag1", "Flag2"],
  "tips": ["Tip1", "Tip2", "Tip3"]
}}
"""
            
            response = self.model.generate_content(prompt)
            strategy = json.loads(response.text.strip())
            logger.info(f"🎯 Generated personalized search strategy")
            return strategy
            
        except Exception as e:
            logger.error(f"Error optimizing search strategy: {e}")
            return {}
    
    async def find_hidden_jobs(self, role: str, location: str = "India") -> List[str]:
        """
        Discover sources for "hidden" or unadvertised jobs
        
        Args:
            role: Job role
            location: Location
        
        Returns:
            List of tips and sources for hidden jobs
        """
        try:
            prompt = f"""
List 10 ways to find "hidden" or unadvertised "{role}" jobs in {location}.

Include:
- Company referral programs
- Cold email strategies
- LinkedIn prospecting techniques
- Twitter job hunting methods
- Industry-specific forums
- Meetup groups
- Alumni networks
- Recruiting agencies specializing in this role

Return as JSON array of actionable tips:
["Tip 1: Description", "Tip 2: Description", ...]
"""
            
            response = self.model.generate_content(prompt)
            tips = json.loads(response.text.strip())
            logger.info(f"🔐 Found {len(tips)} hidden job discovery methods")
            return tips
            
        except Exception as e:
            logger.error(f"Error finding hidden jobs: {e}")
            return []


def get_job_discovery(gemini_client) -> Optional[GeminiJobDiscovery]:
    """
    Create job discovery instance
    
    Args:
        gemini_client: GeminiAI instance
    
    Returns:
        GeminiJobDiscovery instance or None
    """
    if gemini_client:
        return GeminiJobDiscovery(gemini_client)
    return None
