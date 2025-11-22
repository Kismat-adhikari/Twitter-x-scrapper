#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Speed test for the scraper"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime
import time

def test_speed(num_tweets, num_tabs=None):
    """Test scraper speed"""
    print(f"\n{'='*60}")
    print(f"Speed Test: {num_tweets} tweets")
    if num_tabs:
        print(f"Tabs: {num_tabs}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    scraper = TwitterScraper(num_tabs=num_tabs)
    result = scraper.scrape(
        keyword='AI',
        num_tweets=num_tweets,
        job_id=f'speed_test_{datetime.now().strftime("%H%M%S")}',
        search_mode='top'
    )
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    if result:
        tweets_per_second = num_tweets / elapsed
        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"  Time taken: {elapsed:.2f} seconds")
        print(f"  Tweets collected: {num_tweets}")
        print(f"  Speed: {tweets_per_second:.2f} tweets/second")
        print(f"  Speed: {tweets_per_second * 60:.1f} tweets/minute")
        print(f"{'='*60}")
        
        return {
            'tweets': num_tweets,
            'time': elapsed,
            'speed': tweets_per_second
        }
    else:
        print("FAILED: No tweets collected")
        return None

print("Twitter/X Scraper - Speed Test")
print("="*60)

# Test different configurations
results = []

# Test 1: Small batch (10 tweets)
print("\nTest 1: Small batch (10 tweets)")
result = test_speed(10)
if result:
    results.append(result)

# Test 2: Medium batch (50 tweets)
print("\nTest 2: Medium batch (50 tweets)")
result = test_speed(50)
if result:
    results.append(result)

# Test 3: Large batch (100 tweets)
print("\nTest 3: Large batch (100 tweets)")
result = test_speed(100)
if result:
    results.append(result)

# Summary
if results:
    print("\n" + "="*60)
    print("SPEED TEST SUMMARY")
    print("="*60)
    print(f"\n{'Tweets':<10} {'Time (s)':<12} {'Speed (t/s)':<15} {'Speed (t/min)':<15}")
    print("-"*60)
    
    for r in results:
        tweets_per_min = r['speed'] * 60
        print(f"{r['tweets']:<10} {r['time']:<12.2f} {r['speed']:<15.2f} {tweets_per_min:<15.1f}")
    
    # Calculate average
    avg_speed = sum(r['speed'] for r in results) / len(results)
    print("-"*60)
    print(f"Average speed: {avg_speed:.2f} tweets/second ({avg_speed * 60:.1f} tweets/minute)")
    
    # Estimate for larger batches
    print("\n" + "="*60)
    print("ESTIMATED TIME FOR LARGER BATCHES:")
    print("="*60)
    for target in [200, 500, 1000]:
        estimated_time = target / avg_speed
        print(f"  {target} tweets: ~{estimated_time:.1f} seconds (~{estimated_time/60:.1f} minutes)")
