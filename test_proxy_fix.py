#!/usr/bin/env python3
"""Quick test to verify proxy fix works"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime

# Create scraper
scraper = TwitterScraper()

# Test with simple search
job_id = datetime.now().strftime('%Y%m%d_%H%M%S')

print("Testing proxy fix with simple search...")
print("Searching for: 'AI' with 10 tweets")

result = scraper.scrape(
    keyword='AI',
    hashtag='',
    username='',
    num_tweets=10,
    job_id=job_id,
    search_mode='top'
)

if result:
    print(f"\n✅ SUCCESS! File saved: {result}")
else:
    print("\n❌ FAILED - No tweets collected")
