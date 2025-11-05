"""
Gemini AI Integration for Job Scraper Bot
Provides intelligent job analysis, summarization, and natural language processing
"""

import google.generativeai as genai
import os
import logging
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class GeminiAI:
    def __init__(self, api_key: str):
        """Initialize Gemini AI with API key"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✨ Gemini AI initialized successfully")
    
    def summarize_job(self, job: Dict) -> str:
        """
        Create a concise, smart summary of a job posting
        
        Args:
            job: Job dictionary with title, company, location, description, etc.
        
        Returns:
            Formatted summary string with emojis and key highlights
        """
        try:
            prompt = f"""
Analyze this job posting and create a concise, attractive summary in 3-4 bullet points.
Focus on: key requirements, experience level, standout benefits, and red flags (if any).

Job Title: {job.get('title', 'N/A')}
Company: {job.get('company', 'N/A')}
Location: {job.get('location', 'N/A')}
Job Type: {job.get('job_type', 'N/A')}
Description: {job.get('description', 'N/A')[:1000]}

Format:
• First bullet: Key requirements (skills, experience)
• Second bullet: Compensation/Benefits (if mentioned)
• Third bullet: Why this role stands out OR red flags
Keep each bullet under 15 words. Use casual, helpful tone.
"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error summarizing job: {e}")
            return f"• {job.get('title', 'Job')} at {job.get('company', 'Company')}\n• Location: {job.get('location', 'N/A')}\n• Type: {job.get('job_type', 'Full-time')}"
    
    def score_job_quality(self, job: Dict) -> Dict:
        """
        Score a job posting quality (0-10) and provide reasoning
        
        Args:
            job: Job dictionary
        
        Returns:
            Dict with 'score' (int 0-10) and 'reasoning' (str)
        """
        try:
            prompt = f"""
Rate this job posting quality from 0-10 and explain why in ONE sentence.

Job Title: {job.get('title', 'N/A')}
Company: {job.get('company', 'N/A')}
Location: {job.get('location', 'N/A')}
Description: {job.get('description', 'N/A')[:800]}

Consider: clarity, completeness, transparency, red flags, compensation details.

Respond in JSON format:
{{"score": <number 0-10>, "reasoning": "<one sentence explanation>"}}
"""
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return {
                'score': int(result.get('score', 5)),
                'reasoning': result.get('reasoning', 'Standard job posting')
            }
            
        except Exception as e:
            logger.error(f"Error scoring job: {e}")
            return {'score': 5, 'reasoning': 'Unable to analyze'}
    
    def parse_natural_search(self, user_query: str) -> Dict:
        """
        Parse natural language search query into structured filters
        
        Args:
            user_query: Natural language query like "find python jobs in bangalore for freshers"
        
        Returns:
            Dict with extracted filters: role, location, experience, skills, etc.
        """
        try:
            prompt = f"""
Parse this job search query into structured filters.

User Query: "{user_query}"

Extract and respond in JSON:
{{
  "role": "<job role/title>",
  "location": "<city/location>",
  "skills": ["<skill1>", "<skill2>"],
  "experience_level": "<entry/junior/mid/senior>",
  "job_type": "<full-time/part-time/remote/contract>",
  "salary_min": <number or null>,
  "keywords": ["<keyword1>", "<keyword2>"]
}}

If something isn't mentioned, use null. Keep it simple.
"""
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return result
            
        except Exception as e:
            logger.error(f"Error parsing natural search: {e}")
            return {
                'role': user_query,
                'location': None,
                'skills': [],
                'experience_level': None,
                'job_type': None,
                'salary_min': None,
                'keywords': []
            }
    
    def compare_jobs(self, jobs: List[Dict]) -> str:
        """
        Compare multiple jobs and provide recommendation
        
        Args:
            jobs: List of job dictionaries (max 5)
        
        Returns:
            Formatted comparison and recommendation
        """
        try:
            jobs_text = "\n\n".join([
                f"Job {i+1}:\nTitle: {job.get('title')}\nCompany: {job.get('company')}\n"
                f"Location: {job.get('location')}\nDescription: {job.get('description', '')[:300]}"
                for i, job in enumerate(jobs[:5])
            ])
            
            prompt = f"""
Compare these {len(jobs)} jobs and provide:
1. Quick comparison table (key differences)
2. Which one is best for a fresher/entry-level candidate
3. Top recommendation with reasoning (2-3 sentences)

{jobs_text}

Keep it concise and actionable.
"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error comparing jobs: {e}")
            return "Unable to compare jobs. Please review them individually."
    
    def generate_cover_letter(self, job: Dict, user_profile: Dict) -> str:
        """
        Generate a personalized cover letter
        
        Args:
            job: Job dictionary
            user_profile: Dict with user's name, skills, experience
        
        Returns:
            Cover letter text
        """
        try:
            prompt = f"""
Write a concise, professional cover letter (150 words max) for:

Job: {job.get('title')} at {job.get('company')}
Candidate: {user_profile.get('name', 'Job Seeker')}
Skills: {', '.join(user_profile.get('skills', ['data analysis', 'Python', 'SQL']))}
Experience: {user_profile.get('experience', 'Entry-level candidate')}

Make it enthusiastic but professional. Focus on why they're a good fit.
"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return "Unable to generate cover letter at this time."
    
    def extract_skills_from_resume(self, resume_text: str) -> List[str]:
        """
        Extract skills from resume text
        
        Args:
            resume_text: Resume content as string
        
        Returns:
            List of extracted skills
        """
        try:
            prompt = f"""
Extract all technical skills and tools from this resume.

Resume:
{resume_text[:2000]}

Return ONLY a JSON array of skills:
["skill1", "skill2", "skill3"]
"""
            
            response = self.model.generate_content(prompt)
            skills = json.loads(response.text.strip())
            return skills if isinstance(skills, list) else []
            
        except Exception as e:
            logger.error(f"Error extracting skills: {e}")
            return []
    
    def get_interview_questions(self, job: Dict) -> List[str]:
        """
        Generate likely interview questions for a job
        
        Args:
            job: Job dictionary
        
        Returns:
            List of interview questions
        """
        try:
            prompt = f"""
Generate 5 likely interview questions for this role:

Job: {job.get('title')} at {job.get('company')}
Description: {job.get('description', '')[:600]}

Return as JSON array:
["Question 1?", "Question 2?", ...]
"""
            
            response = self.model.generate_content(prompt)
            questions = json.loads(response.text.strip())
            return questions if isinstance(questions, list) else []
            
        except Exception as e:
            logger.error(f"Error generating interview questions: {e}")
            return [
                "Tell me about yourself.",
                "Why do you want this role?",
                "What are your key strengths?",
                "Describe a challenging project you've worked on.",
                "Where do you see yourself in 5 years?"
            ]
    
    def estimate_salary(self, job: Dict) -> Dict:
        """
        Estimate salary range based on job title, company, and location
        
        Args:
            job: Job dictionary with title, company, location
        
        Returns:
            Dict with salary_min, salary_max, currency, confidence, reasoning
        """
        try:
            prompt = f"""
Based on Indian job market data, estimate the salary range for this position:

Job Title: {job.get('title', 'N/A')}
Company: {job.get('company', 'N/A')}
Location: {job.get('location', 'India')}
Description snippet: {job.get('description', '')[:300]}

Consider:
- Job title and seniority level
- Company (if known/recognizable)
- Location (metro vs tier-2 city)
- Industry standards in India
- Experience level implied

Return as JSON:
{{
  "salary_min": <number in LPA>,
  "salary_max": <number in LPA>,
  "currency": "INR",
  "confidence": "High/Medium/Low",
  "reasoning": "<one sentence why this estimate>"
}}

If entry-level/fresher role, estimate 3-8 LPA.
If mid-level, estimate 8-20 LPA.
If senior, estimate 20-40+ LPA.
"""
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return {
                'salary_min': result.get('salary_min', 0),
                'salary_max': result.get('salary_max', 0),
                'currency': result.get('currency', 'INR'),
                'confidence': result.get('confidence', 'Medium'),
                'reasoning': result.get('reasoning', 'Market estimate')
            }
            
        except Exception as e:
            logger.error(f"Error estimating salary: {e}")
            return {
                'salary_min': 0,
                'salary_max': 0,
                'currency': 'INR',
                'confidence': 'Low',
                'reasoning': 'Unable to estimate'
            }
    
    def analyze_company(self, company_name: str) -> Dict:
        """
        Get insights about a company
        
        Args:
            company_name: Name of the company
        
        Returns:
            Dict with company insights
        """
        try:
            prompt = f"""
Provide brief insights about this company for a job seeker:

Company: {company_name}

Include (if known):
1. Company type (Startup/MNC/Product/Service)
2. Industry/Domain
3. Company size (Small/Medium/Large)
4. Known for (products/culture/reputation)
5. Average salary reputation (Competitive/Average/Below-average)
6. Work-life balance reputation (Good/Average/Poor)
7. Growth opportunities (Excellent/Good/Limited)

Return as JSON:
{{
  "type": "Startup/MNC/Product/Service/Unknown",
  "industry": "Industry name",
  "size": "Small/Medium/Large/Unknown",
  "known_for": "Brief description",
  "salary_reputation": "Competitive/Average/Below-average/Unknown",
  "work_life_balance": "Good/Average/Poor/Unknown",
  "growth_opportunities": "Excellent/Good/Limited/Unknown",
  "recommendation": "2-3 sentence advice for job seeker"
}}

If company is unknown, mark fields as "Unknown" and be honest about it.
"""
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing company: {e}")
            return {
                'type': 'Unknown',
                'industry': 'Unknown',
                'size': 'Unknown',
                'known_for': 'No information available',
                'salary_reputation': 'Unknown',
                'work_life_balance': 'Unknown',
                'growth_opportunities': 'Unknown',
                'recommendation': 'Research this company before applying.'
            }
    
    def predict_application_success(self, job: Dict, user_profile: Dict) -> Dict:
        """
        Predict likelihood of getting this job based on user profile
        
        Args:
            job: Job dictionary
            user_profile: User's skills, experience, etc.
        
        Returns:
            Dict with success_rate, strengths, gaps, tips
        """
        try:
            prompt = f"""
Assess the match between this job and candidate:

Job: {job.get('title', 'N/A')} at {job.get('company', 'N/A')}
Requirements: {job.get('description', 'N/A')[:500]}

Candidate:
- Experience: {user_profile.get('experience', 'Entry-level')}
- Skills: {', '.join(user_profile.get('skills', []))}
- Education: {user_profile.get('education', 'Bachelor\'s degree')}

Provide:
1. Match percentage (0-100)
2. Key strengths (what they have)
3. Skill gaps (what they're missing)
4. Application tips

Return as JSON:
{{
  "match_percentage": <0-100>,
  "strengths": ["strength1", "strength2"],
  "gaps": ["gap1", "gap2"],
  "tips": ["tip1", "tip2"],
  "should_apply": true/false,
  "reasoning": "One sentence why"
}}
"""
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return result
            
        except Exception as e:
            logger.error(f"Error predicting success: {e}")
            return {
                'match_percentage': 50,
                'strengths': [],
                'gaps': [],
                'tips': ['Review job requirements carefully'],
                'should_apply': True,
                'reasoning': 'Unable to assess match'
            }
    
    def extract_hidden_requirements(self, job: Dict) -> Dict:
        """
        Extract unstated requirements from job description
        
        Args:
            job: Job dictionary
        
        Returns:
            Dict with explicit and implicit requirements
        """
        try:
            prompt = f"""
Analyze this job posting and identify both stated and UNSTATED requirements:

Job: {job.get('title', 'N/A')}
Description: {job.get('description', 'N/A')[:800]}

Extract:
1. Explicit requirements (clearly stated)
2. Implicit requirements (reading between the lines)
3. Nice-to-have skills
4. Cultural fit expectations
5. Red flags or unrealistic expectations

Return as JSON:
{{
  "explicit_skills": ["skill1", "skill2"],
  "implicit_skills": ["skill1", "skill2"],
  "nice_to_have": ["skill1", "skill2"],
  "cultural_fit": "Description of expected culture fit",
  "red_flags": ["flag1", "flag2"] or [],
  "realistic": true/false,
  "advice": "One sentence advice"
}}
"""
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return result
            
        except Exception as e:
            logger.error(f"Error extracting requirements: {e}")
            return {
                'explicit_skills': [],
                'implicit_skills': [],
                'nice_to_have': [],
                'cultural_fit': 'Unknown',
                'red_flags': [],
                'realistic': True,
                'advice': 'Read the job description carefully'
            }
    
    def estimate_competition(self, job: Dict) -> Dict:
        """
        Estimate competition level for a job
        
        Args:
            job: Job dictionary
        
        Returns:
            Dict with competition analysis
        """
        try:
            prompt = f"""
Estimate the competition level for this job in India:

Job: {job.get('title', 'N/A')}
Company: {job.get('company', 'N/A')}
Location: {job.get('location', 'N/A')}

Consider:
- Job popularity (how many people want this role)
- Location attractiveness
- Company reputation
- Experience level required
- Skill specificity

Return as JSON:
{{
  "competition": "Very High/High/Medium/Low",
  "estimated_applicants": "100-500/50-100/10-50/<10",
  "quick_apply_advantage": true/false,
  "best_time": "Morning/Evening/Weekend",
  "advice": "One sentence strategy tip"
}}
"""
            
            response = self.model.generate_content(prompt)
            result = json.loads(response.text.strip())
            return result
            
        except Exception as e:
            logger.error(f"Error estimating competition: {e}")
            return {
                'competition': 'Medium',
                'estimated_applicants': '50-100',
                'quick_apply_advantage': True,
                'best_time': 'Morning',
                'advice': 'Apply quickly for better visibility'
            }


# Singleton instance
_gemini_instance = None

def get_gemini_ai(api_key: Optional[str] = None) -> Optional[GeminiAI]:
    """
    Get or create Gemini AI instance
    
    Args:
        api_key: Gemini API key (reads from env if not provided)
    
    Returns:
        GeminiAI instance or None if no API key
    """
    global _gemini_instance
    
    if _gemini_instance is None:
        key = api_key or os.getenv('GEMINI_API_KEY')
        if key:
            _gemini_instance = GeminiAI(key)
        else:
            logger.warning("⚠️ No Gemini API key found. AI features disabled.")
    
    return _gemini_instance
