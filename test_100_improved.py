#!/usr/bin/env python3
"""
🧪 Test improved 100 tweet collection
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.playwright_scraper import TwitterScraper

def test_100_tweets():
    """Test collecting exactly 100 tweets"""
    print("🧪 Testing improved 100 tweet collection")
    print("=" * 50)
    
    # Test parameters
    keyword = "AI"
    num_tweets = 100
    
    # Initialize scraper 
    scraper = TwitterScraper()
    # Disable broken proxies
    scraper.proxy_manager.proxies = []
    
    # Start timing
    start_time = time.time()
    print(f"⏰ Started at: {time.strftime('%H:%M:%S')}")
    print(f"🎯 Target: {num_tweets} tweets")
    
    try:
        # Run scraping
        filename = scraper.scrape(
            keyword=keyword,
            num_tweets=num_tweets,
            job_id="test_100_improved",
            search_mode='top'
        )
        
        # Calculate time
        end_time = time.time()
        total_time = end_time - start_time
        
        print("=" * 50)
        print("📊 100 TWEET TEST RESULTS:")
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"📁 File: {filename}")
        
        if filename:
            # Check if we got closer to 100
            try:
                with open(f"scraped_data/{filename}", 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
                    actual_count = len(lines) - 1  # Minus header
                
                success_rate = (actual_count / num_tweets) * 100
                print(f"📊 Tweets collected: {actual_count}/{num_tweets}")
                print(f"📈 Success rate: {success_rate:.1f}%")
                
                if actual_count >= 90:
                    print("✅ EXCELLENT! 90%+ collection rate")
                elif actual_count >= 80:
                    print("✅ GOOD! 80%+ collection rate") 
                elif actual_count >= 70:
                    print("⚠️  FAIR - 70%+ but needs improvement")
                else:
                    print("❌ POOR - Less than 70% collection rate")
                    
                print(f"🚀 Speed: {actual_count/total_time:.1f} tweets/second")
                
            except Exception as e:
                print(f"⚠️  Could not read file: {e}")
        else:
            print("❌ No file created")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_100_tweets()