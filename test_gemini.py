#!/usr/bin/env python3
"""
Quick test script to check Gemini API status and quota
"""
import os
import sys
from gemini_ai import get_gemini_ai

def test_gemini():
    """Test Gemini API connection and basic functionality"""
    
    print("🔍 Testing Gemini API...")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY not found in environment variables!")
        print("Please set it with: $env:GEMINI_API_KEY='your-key-here'")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-5:]}")
    
    # Initialize Gemini
    try:
        print("\n🤖 Initializing Gemini AI...")
        gemini = get_gemini_ai()
        if not gemini:
            print("❌ Failed to initialize Gemini AI!")
            return False
        print("✅ Gemini AI initialized successfully!")
    except Exception as e:
        print(f"❌ Error initializing Gemini: {e}")
        return False
    
    # Test basic summarization
    try:
        print("\n📝 Testing job summarization...")
        test_job = {
            'title': 'Senior Python Developer',
            'company': 'Test Corp',
            'location': 'Delhi, India',
            'description': 'We are looking for an experienced Python developer to join our team. Must have 3+ years of experience with Django, FastAPI, and PostgreSQL.',
            'salary': '15-20 LPA',
            'site': 'Test'
        }
        
        summary = gemini.summarize_job(test_job)
        print("✅ Summary generated successfully!")
        print(f"\nSummary:\n{summary}\n")
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error generating summary: {error_msg}")
        
        # Check for specific errors
        if 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
            print("\n⚠️  QUOTA EXCEEDED!")
            print("Your Gemini API has reached its daily/monthly limit.")
            print("\nFree tier limits:")
            print("  • 15 requests per minute")
            print("  • 1,500 requests per day")
            print("\nSolutions:")
            print("  1. Wait for quota to reset (resets daily)")
            print("  2. Disable some AI features in config.yaml")
            print("  3. Upgrade to paid tier (very cheap)")
        elif 'api key' in error_msg.lower() or 'authentication' in error_msg.lower():
            print("\n⚠️  API KEY ERROR!")
            print("Your API key may be invalid or expired.")
            print("Get a new one from: https://makersuite.google.com/app/apikey")
        
        return False
    
    # Test quality scoring
    try:
        print("⭐ Testing quality scoring...")
        score_data = gemini.score_job_quality(test_job)
        print(f"✅ Quality score: {score_data.get('score')}/10")
        print(f"   Reason: {score_data.get('reason', 'N/A')[:100]}...")
        
    except Exception as e:
        print(f"⚠️  Scoring test failed (quota may be low): {e}")
    
    print("\n" + "=" * 60)
    print("✅ Gemini API is working!")
    print("\nIf you're not seeing AI summaries in Telegram:")
    print("  1. Check Railway logs for quota errors")
    print("  2. Ensure GEMINI_API_KEY is set in Railway environment variables")
    print("  3. Verify 'job_summarization: true' in config.yaml")
    print("  4. Check that 'gemini.enabled: true' in config.yaml")
    
    return True

if __name__ == "__main__":
    try:
        success = test_gemini()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
