#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script to see API structure"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime

print("Running debug scrape to see API structure...")
print("=" * 60)

scraper = TwitterScraper(num_tabs=1)
result = scraper.scrape(
    keyword='AI',
    num_tweets=3,
    job_id=f'debug_{datetime.now().strftime("%H%M%S")}',
    search_mode='top'
)

print("\n" + "=" * 60)
print("Debug complete. Check output above for DEBUG messages.")
