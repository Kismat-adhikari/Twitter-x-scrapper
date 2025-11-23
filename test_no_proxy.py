#!/usr/bin/env python3
"""Test scraper without proxies to isolate the issue"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime

# Create scraper
scraper = TwitterScraper()

# Disable proxies by clearing the proxy manager
scraper.proxy_manager.proxies = []

# Test with simple search
job_id = datetime.now().strftime('%Y%m%d_%H%M%S')

print("Testing WITHOUT proxies...")
print("Searching for: 'AI' with 10 tweets")
print("=" * 50)

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
