# 🤖 Gemini AI Features

Your job scraper bot now has AI superpowers powered by Google's Gemini API! ✨

## 🎯 What's New?

### 1. **Smart Job Summaries**
Every job notification now includes an AI-generated summary that highlights:
- Key requirements and skills needed
- Compensation and benefits (if mentioned)
- Why the role stands out or potential red flags

**Before:**
```
🔔 New Job Alert!
Title: Data Analyst
Company: ABC Corp
Location: Bangalore
[Long description...]
```

**After with Gemini:**
```
🔔 New Job Alert! ⭐
Title: Data Analyst
Company: ABC Corp
Location: Bangalore

✨ AI Summary:
• Needs Python, SQL, 0-2 years exp
• Offers training + mentorship for freshers
• Great for entry-level, flexible work culture

📊 Quality Score: 8/10
```

### 2. **Natural Language Search** 
Use the `/find` command to search using plain English:

```
/find python jobs in bangalore for freshers
/find remote data analyst positions
/find entry level business analyst in mumbai
/find junior developer roles under 5 LPA
```

The AI understands your intent and extracts:
- Job role
- Location
- Experience level
- Skills required
- Salary expectations

### 3. **Job Quality Scoring**
Each job gets a quality score (0-10) based on:
- Completeness of job description
- Transparency about requirements
- Clarity of compensation
- Red flags (vague descriptions, unrealistic requirements)

High-quality jobs (8+) get a 🌟 star!

## 🚀 Setup

### 1. Get Your Free Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your key

### 2. Add to Railway Environment Variables

In Railway dashboard:
1. Go to your project → Variables tab
2. Add new variable:
   - **Name:** `GEMINI_API_KEY`
   - **Value:** Your API key from step 1
3. Share with your "web" service
4. Railway will auto-redeploy

### 3. Configure Features (config.yaml)

```yaml
gemini:
  enabled: true
  features:
    job_summarization: true           # Smart summaries (recommended)
    natural_language_search: true     # /find command (recommended)
    job_quality_scoring: true         # 0-10 ratings (recommended)
    job_comparison: false             # Compare jobs (more API calls)
    cover_letter_generation: false    # Auto cover letters (more API calls)
    interview_questions: false        # Interview prep (more API calls)
```

## 💰 Cost

- **Free Tier:** 60 requests/minute, 1500 requests/day
- **Your Usage:** ~2-10 requests per job (with default settings)
- **Estimate:** Easily handles 100-500 jobs/day for FREE
- **Monthly Cost:** ₹0 with normal usage on free tier

## 📊 Feature Comparison

| Feature | Without AI | With Gemini AI |
|---------|-----------|----------------|
| Job Summaries | ❌ Long descriptions | ✅ 3-bullet key points |
| Search | 🔍 Menu-based | ✨ Natural language |
| Quality Check | ❌ Manual review | ✅ Auto-scored 0-10 |
| Notifications | 📧 Standard | 🌟 Smart + scored |

## 🎨 Bot Commands

### Regular Commands
- `/start` - Welcome message
- `/search` - Guided job search (menu-based)
- `/status` - Check your active search
- `/stop` - Stop searching
- `/help` - Show help

### AI Commands (New!)
- `/find <query>` - Natural language search
  - Example: `/find remote python jobs for freshers`

## 🔧 Advanced Features (Coming Soon)

Want more? Enable these in config:

### Job Comparison
```
/compare
```
Compare your last 3-5 job matches side-by-side with pros/cons analysis.

### Cover Letter Generation
```
/cover <job_number>
```
Generate a personalized cover letter for a specific job.

### Interview Prep
```
/prep <job_number>
```
Get likely interview questions and sample answers for a role.

## 🐛 Troubleshooting

### "AI search is not available"
- Check that `GEMINI_API_KEY` is set in Railway
- Verify `gemini.enabled: true` in config.yaml
- Check Railway logs for initialization errors

### Quality scores not showing
- Enable `job_quality_scoring: true` in config
- Scores only show for high-quality (8+) or mid-quality (6-7) jobs

### Natural language search not working
- Use complete sentences: "find X jobs in Y for Z"
- Enable `natural_language_search: true` in config
- Check Gemini API quota (free tier: 1500/day)

## 📈 Performance Tips

1. **Start with essentials:**
   - Enable: summarization, scoring, natural_language_search
   - Disable: comparison, cover_letter, interview_questions

2. **Monitor API usage:**
   - Check [Google AI Studio](https://makersuite.google.com) dashboard
   - Free tier is usually enough for personal use

3. **Upgrade if needed:**
   - If you hit limits, consider Gemini Pro plan
   - Or disable some features to reduce API calls

## 🎉 Enjoy Your Smart Job Bot!

Your bot is now way smarter than before. It understands natural language, provides intelligent summaries, and helps you find better jobs faster!

Questions? Check the logs or open an issue on GitHub.
