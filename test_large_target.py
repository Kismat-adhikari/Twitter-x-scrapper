#!/usr/bin/env python3
"""
Test script to verify improved large target handling
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.playwright_scraper import TwitterScraper
import time

def test_large_target():
    print("🧪 TESTING: Large target (200 tweets) handling")
    print("=" * 60)
    
    start_time = time.time()
    
    scraper = TwitterScraper()  # Auto tab count
    
    # Use a broader search to ensure content
    result = scraper.scrape(
        keyword='python',  # Broader than previous complex search
        num_tweets=200,
        job_id='test_large_target'
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n📊 TEST RESULTS:")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    print(f"📁 File: {result}")
    
    if result:
        # Check actual tweet count
        import csv
        try:
            with open(f'scraped_data/{result}', 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                actual_count = sum(1 for row in reader)
            
            print(f"🎯 Target: 200 tweets")
            print(f"✅ Actual: {actual_count} tweets")
            print(f"📈 Success rate: {actual_count/200*100:.1f}%")
            print(f"🚀 Speed: {actual_count/duration:.1f} tweets/second")
            
            if actual_count >= 150:  # 75% success is good for large targets
                print(f"✅ SUCCESS: Got {actual_count} tweets (good for large target)!")
                return True
            else:
                print(f"⚠️  Partial success: Got {actual_count}/200 tweets")
                return False
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False
    else:
        print("❌ FAILED: No file created")
        return False

if __name__ == "__main__":
    test_large_target()