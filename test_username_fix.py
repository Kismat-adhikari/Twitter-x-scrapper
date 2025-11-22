#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple test to verify username extraction"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime
import csv

print("Testing username extraction...")
print("=" * 60)

scraper = TwitterScraper(num_tabs=1)
result = scraper.scrape(
    keyword='AI',
    num_tweets=5,
    job_id=f'test_user_{datetime.now().strftime("%H%M%S")}',
    search_mode='top'
)

if result:
    csv_path = f"scraped_data/{result}"
    print(f"\nChecking CSV: {csv_path}")
    print("=" * 60)
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            username = row.get('username', 'N/A')
            likes = row.get('likes', '0')
            text = row.get('text', '')[:50]
            
            print(f"{i}. @{username} - {likes} likes")
            print(f"   {text}...")
            
            if i >= 5:
                break
    
    print("\n" + "=" * 60)
    
    # Count unknowns
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        total = 0
        unknown = 0
        for row in reader:
            total += 1
            if row.get('username') == 'unknown':
                unknown += 1
    
    print(f"Total tweets: {total}")
    print(f"Unknown usernames: {unknown}")
    print(f"Known usernames: {total - unknown}")
    
    if unknown == 0:
        print("\nSUCCESS: All usernames extracted!")
    elif unknown < total:
        print(f"\nPARTIAL: {total - unknown}/{total} usernames extracted")
    else:
        print("\nFAILED: All usernames are 'unknown'")
else:
    print("FAILED: No tweets collected")
