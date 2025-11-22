#!/usr/bin/env python3
"""
🧪 TEST STANDARD MODE: Test the regular scraper to ensure it works
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.playwright_scraper import TwitterScraper

def test_standard_mode():
    """Test scraper in standard mode"""
    print("🧪 TESTING STANDARD MODE: 20 tweets")
    print("=" * 50)
    
    # Test parameters (smaller number to test standard mode)
    keyword = "AI"
    num_tweets = 20  # Small number to avoid turbo mode
    
    # Initialize scraper and disable turbo mode temporarily
    scraper = TwitterScraper()
    scraper.turbo_mode = False  # Force standard mode
    
    # Start timing
    start_time = time.time()
    print(f"⏰ Started at: {time.strftime('%H:%M:%S')}")
    
    try:
        # Run scraping
        filename = scraper.scrape(
            keyword=keyword,
            num_tweets=num_tweets,
            job_id="standard_test"
        )
        
        # Calculate time
        end_time = time.time()
        total_time = end_time - start_time
        
        print("=" * 50)
        print("📊 STANDARD MODE RESULTS:")
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"📁 File: {filename}")
        
        if filename:
            print("✅ SUCCESS: Standard mode working!")
            # Check CSV content
            try:
                import csv
                csv_path = f'scraped_data/{filename}'
                with open(csv_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    tweets = list(reader)
                    print(f"📊 Tweets in file: {len(tweets)}")
                    
                    if tweets:
                        print("\n📝 Sample tweet:")
                        tweet = tweets[0]
                        print(f"Text: {tweet.get('text', '')[:100]}...")
                        print(f"Username: {tweet.get('username', '')}")
                        print(f"Hashtags: {tweet.get('hashtags', '')}")
                        print(f"Mentions: {tweet.get('mentions', '')}")
                        print(f"Likes: {tweet.get('likes', '')}")
            except Exception as e:
                print(f"Error reading CSV: {e}")
        else:
            print("❌ FAILED: No tweets collected in standard mode")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_standard_mode()