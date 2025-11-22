#!/usr/bin/env python3
"""
🚀 PERFORMANCE TEST SCRIPT
Test the optimized Twitter scraper to achieve <1 minute for 100 tweets
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.playwright_scraper import TwitterScraper

def test_performance():
    """Test scraper performance"""
    print("🧪 PERFORMANCE TEST: 100 tweets in <1 minute")
    print("=" * 50)
    
    # Test parameters
    keyword = "artificial intelligence"  # Popular topic for quick results
    num_tweets = 100
    
    # Initialize scraper
    scraper = TwitterScraper()
    
    # Start timing
    start_time = time.time()
    print(f"⏰ Started at: {time.strftime('%H:%M:%S')}")
    
    try:
        # Run scraping
        filename = scraper.scrape(
            keyword=keyword,
            num_tweets=num_tweets,
            job_id="performance_test"
        )
        
        # Calculate time
        end_time = time.time()
        total_time = end_time - start_time
        
        print("=" * 50)
        print("📊 PERFORMANCE RESULTS:")
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"🎯 Target: <60 seconds")
        print(f"📁 File: {filename}")
        
        if total_time < 60:
            print("✅ SUCCESS: Under 1 minute achieved!")
            print(f"🚀 Speed: {num_tweets/total_time:.1f} tweets/second")
        else:
            print("⚠️  NEEDS OPTIMIZATION: Over 1 minute")
            
        # Calculate tweets per minute
        tweets_per_minute = (num_tweets / total_time) * 60
        print(f"📈 Rate: {tweets_per_minute:.0f} tweets/minute")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_performance()