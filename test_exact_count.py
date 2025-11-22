#!/usr/bin/env python3
"""Test exact tweet count"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime
import csv

target = 20
print(f"Testing exact count: Target = {target} tweets")
print("=" * 60)

scraper = TwitterScraper(num_tabs=2)
result = scraper.scrape(
    keyword='AI',
    num_tweets=target,
    job_id=f'exact_count_{datetime.now().strftime("%H%M%S")}',
    search_mode='top'
)

if result:
    csv_path = f"scraped_data/{result}"
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        actual = sum(1 for _ in reader)
    
    print("\n" + "=" * 60)
    print(f"Target: {target} tweets")
    print(f"Actual: {actual} tweets")
    print(f"Difference: {actual - target}")
    
    if actual == target:
        print("\nSUCCESS: Exact count!")
    elif actual <= target + 2:
        print("\nACCEPTABLE: Within 2 tweets of target")
    else:
        print(f"\nFAILED: {actual - target} extra tweets")
else:
    print("FAILED: No tweets collected")
