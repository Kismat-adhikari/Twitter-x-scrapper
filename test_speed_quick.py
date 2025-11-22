#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick speed test"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime
import time

def quick_test(num_tweets):
    """Quick speed test"""
    print(f"\nTesting {num_tweets} tweets...")
    
    start_time = time.time()
    
    scraper = TwitterScraper()
    result = scraper.scrape(
        keyword='AI',
        num_tweets=num_tweets,
        job_id=f'quick_{datetime.now().strftime("%H%M%S")}',
        search_mode='top'
    )
    
    elapsed = time.time() - start_time
    
    if result:
        speed = num_tweets / elapsed
        print(f"\nRESULTS:")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Speed: {speed:.2f} tweets/sec ({speed*60:.1f} tweets/min)")
        return speed
    return 0

print("Quick Speed Test")
print("="*60)

# Test 50 tweets
speed = quick_test(50)

if speed > 0:
    print(f"\n{'='*60}")
    print(f"ESTIMATED TIMES:")
    print(f"  100 tweets: ~{100/speed:.1f} seconds")
    print(f"  200 tweets: ~{200/speed:.1f} seconds (~{200/speed/60:.1f} min)")
    print(f"  500 tweets: ~{500/speed:.1f} seconds (~{500/speed/60:.1f} min)")
