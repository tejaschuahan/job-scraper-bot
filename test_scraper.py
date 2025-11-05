"""Test version of job scraper - runs one cycle only"""
import asyncio
import sys
sys.path.insert(0, 'e:/bot')

from job_scraper import JobScraper
import yaml

async def test_scraper():
    """Run one scraping cycle for testing"""
    print("=" * 60)
    print("🧪 JOB SCRAPER TEST MODE")
    print("=" * 60)
    
    # Load configuration
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Display settings
    print(f"\n📋 Configuration:")
    print(f"   Queries: {', '.join(config['search']['queries'])}")
    print(f"   Enabled sites: {[k for k, v in config['sites'].items() if v.get('enabled')]}")
    
    # Initialize scraper
    print(f"\n🚀 Initializing scraper...")
    scraper = JobScraper(config)
    
    # Create aiohttp session
    import aiohttp
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
    scraper.session = aiohttp.ClientSession(
        timeout=timeout,
        connector=connector
    )
    
    try:
        print(f"\n🔍 Starting single scraping cycle...")
        print(f"   (This will take 15-30 seconds)\n")
        
        # Run one cycle
        queries = config.get('search', {}).get('queries', [])
        await scraper.run_scraping_cycle(queries)
        
        # Show results
        print(f"\n" + "=" * 60)
        print(f"📊 TEST RESULTS:")
        print(f"=" * 60)
        print(scraper.stats.get_summary())
        print(f"\n✅ Test complete! Check your Telegram for any new job notifications.")
        print(f"\n💡 To run continuously (24/7), use: python job_scraper.py")
        
    finally:
        await scraper.session.close()

if __name__ == "__main__":
    asyncio.run(test_scraper())
