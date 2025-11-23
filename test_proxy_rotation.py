#!/usr/bin/env python3
"""
🧪 Test proxy rotation to see if each tab gets different proxies
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.playwright_scraper import TwitterScraper

def test_proxy_rotation():
    """Test if proxy rotation is working correctly"""
    print("🧪 Testing proxy rotation with 3 tabs")
    print("=" * 50)
    
    # Test parameters
    keyword = "crypto"
    num_tweets = 10  # Small number to test quickly
    
    # Initialize scraper with 3 tabs
    scraper = TwitterScraper(num_tabs=3)
    scraper.turbo_mode = False  # Force standard mode
    
    # Start timing
    start_time = time.time()
    print(f"⏰ Started at: {time.strftime('%H:%M:%S')}")
    
    try:
        # Run scraping
        filename = scraper.scrape(
            keyword=keyword,
            num_tweets=num_tweets,
            job_id="proxy_test",
            search_mode='top'
        )
        
        # Calculate time
        end_time = time.time()
        total_time = end_time - start_time
        
        print("=" * 50)
        print("📊 PROXY ROTATION TEST RESULTS:")
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"📁 File: {filename}")
        
        if filename:
            # Count tweets in file
            try:
                with open(f"scraped_data/{filename}", 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
                    actual_count = len(lines) - 1  # Minus header
                print(f"📊 Tweets collected: {actual_count}")
                
                if actual_count > 0:
                    print("✅ Proxy rotation test successful!")
                else:
                    print("❌ No tweets collected - possible proxy/blocking issues")
            except Exception as e:
                print(f"⚠️  Could not read file: {e}")
        else:
            print("❌ No file created - proxy rotation or scraping failed")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_proxy_rotation()