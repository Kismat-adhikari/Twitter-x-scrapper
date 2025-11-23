#!/usr/bin/env python3
"""
🧪 Test without proxies to see if the issue is proxy-related
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.playwright_scraper import TwitterScraper

def test_no_proxy():
    """Test without proxies to isolate the issue"""
    print("🧪 Testing without proxies")
    print("=" * 50)
    
    # Use very simple search terms
    keyword = "bitcoin"  # Popular keyword
    num_tweets = 3  # Very small number
    
    # Initialize scraper
    scraper = TwitterScraper(num_tabs=1)  # Use only 1 tab
    
    # Disable proxy usage temporarily
    original_proxies = scraper.proxy_manager.proxies
    scraper.proxy_manager.proxies = []  # Empty proxy list
    
    # Start timing
    start_time = time.time()
    print(f"⏰ Started at: {time.strftime('%H:%M:%S')}")
    
    try:
        # Run scraping without proxies
        filename = scraper.scrape(
            keyword=keyword,
            num_tweets=num_tweets,
            job_id="no_proxy_test",
            search_mode='top'
        )
        
        # Calculate time
        end_time = time.time()
        total_time = end_time - start_time
        
        print("=" * 50)
        print("📊 NO PROXY TEST RESULTS:")
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"📁 File: {filename}")
        
        if filename:
            # Check if file has content
            try:
                with open(f"scraped_data/{filename}", 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
                    actual_count = len(lines) - 1  # Minus header
                
                print(f"📊 Tweets in file: {actual_count}")
                
                if actual_count > 0:
                    print("✅ No proxy test successful - ISSUE IS WITH PROXIES!")
                else:
                    print("❌ No tweets even without proxies - may be a broader issue")
            except Exception as e:
                print(f"⚠️  Could not read file: {e}")
        else:
            print("❌ No file even without proxies - broader authentication issue")
            
        # Restore proxy list
        scraper.proxy_manager.proxies = original_proxies
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        # Restore proxy list
        scraper.proxy_manager.proxies = original_proxies

if __name__ == "__main__":
    test_no_proxy()