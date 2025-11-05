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
