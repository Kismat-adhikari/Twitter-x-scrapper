#!/usr/bin/env python3
"""
Test script to verify 100 tweet collection
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.playwright_scraper import TwitterScraper
import time

def test_100_tweets():
    print("🧪 TESTING: 100 tweet collection")
    print("=" * 50)
    
    start_time = time.time()
    
    scraper = TwitterScraper()  # Let it auto-determine tab count
    
    # Test with a popular keyword to ensure content availability
    result = scraper.scrape(
        keyword='AI',
        num_tweets=100,
        job_id='test_100_tweets'
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n📊 TEST RESULTS:")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    print(f"📁 File: {result}")
    
    if result:
        # Check actual tweet count
        import csv
        with open(f'scraped_data/{result}', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            actual_count = sum(1 for row in reader)
        
        print(f"🎯 Target: 100 tweets")
        print(f"✅ Actual: {actual_count} tweets")
        print(f"📈 Success rate: {actual_count/100*100:.1f}%")
        
        if actual_count < 100:
            print(f"❌ ISSUE: Only got {actual_count}/100 tweets")
            return False
        else:
            print(f"✅ SUCCESS: Got {actual_count} tweets!")
            return True
    else:
        print("❌ FAILED: No file created")
        return False

if __name__ == "__main__":
    test_100_tweets()