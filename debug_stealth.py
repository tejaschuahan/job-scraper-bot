"""
Debug script to test stealth browser and see actual page content
"""
import asyncio
from pathlib import Path
from stealth_scrapers import StealthBrowserScraper

async def test_indeed():
    """Test Indeed with stealth browser and save screenshot"""
    print("Testing Indeed stealth scraper...")
    
    scraper = StealthBrowserScraper()
    await scraper.init_browser(headless=False)  # Visible browser for debugging
    
    page = await scraper.create_stealth_page()
    
    url = "https://www.indeed.com/jobs?q=data+analyst&fromage=1&sort=date"
    print(f"Loading: {url}")
    
    await page.goto(url, wait_until='load', timeout=60000)
    await asyncio.sleep(5)
    
    # Save screenshot
    await page.screenshot(path="indeed_debug.png", full_page=True)
    print("Screenshot saved: indeed_debug.png")
    
    # Save HTML
    content = await page.content()
    with open("indeed_debug.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("HTML saved: indeed_debug.html")
    
    # Check for captcha/blocking
    if "captcha" in content.lower() or "robot" in content.lower():
        print("⚠️ CAPTCHA or bot detection found!")
    else:
        print("✅ No obvious blocking detected")
    
    await scraper.close()

async def test_glassdoor():
    """Test Glassdoor with stealth browser"""
    print("\nTesting Glassdoor stealth scraper...")
    
    scraper = StealthBrowserScraper()
    await scraper.init_browser(headless=False)
    
    page = await scraper.create_stealth_page()
    
    url = "https://www.glassdoor.com/Job/jobs.htm?sc.keyword=data+analyst"
    print(f"Loading: {url}")
    
    await page.goto(url, wait_until='load', timeout=60000)
    await asyncio.sleep(5)
    
    # Save screenshot
    await page.screenshot(path="glassdoor_debug.png", full_page=True)
    print("Screenshot saved: glassdoor_debug.png")
    
    # Save HTML
    content = await page.content()
    with open("glassdoor_debug.html", "w", encoding="utf-8") as f:
        f.write(content)
    print("HTML saved: glassdoor_debug.html")
    
    # Check for Cloudflare
    if "cloudflare" in content.lower() or "challenge" in content.lower():
        print("⚠️ Cloudflare challenge detected!")
    else:
        print("✅ No Cloudflare blocking detected")
    
    await scraper.close()

async def main():
    """Run all tests"""
    try:
        await test_indeed()
        await test_glassdoor()
        print("\n✅ Debug complete! Check the .png and .html files.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
