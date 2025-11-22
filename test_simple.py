#!/usr/bin/env python3
"""
🧪 SIMPLE TEST: Test with a small number to see engagement metrics working
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.playwright_scraper import TwitterScraper

def test_simple():
    """Simple test with just 5 tweets to debug engagement metrics"""
    print("🧪 SIMPLE TEST: 5 tweets with engagement metrics debug")
    print("=" * 50)
    
    # Test parameters
    keyword = "AI"
    num_tweets = 5  # Very small number for debugging
    
    # Initialize scraper
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
            job_id="simple_test"
        )
        
        # Calculate time
        end_time = time.time()
        total_time = end_time - start_time
        
        print("=" * 50)
        print("📊 SIMPLE TEST RESULTS:")
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"📁 File: {filename}")
        
        if filename:
            # Read and analyze CSV content
            try:
                import csv
                csv_path = f'scraped_data/{filename}'
                with open(csv_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    tweets = list(reader)
                    print(f"📊 Tweets in file: {len(tweets)}")
                    
                    if tweets:
                        print("\\n📝 DETAILED ANALYSIS:")
                        for i, tweet in enumerate(tweets):
                            print(f"\\n--- Tweet {i+1} ---")
                            print(f"Text: {tweet.get('text', '')[:80]}...")
                            print(f"Username: @{tweet.get('username', '')}")
                            print(f"Likes: '{tweet.get('likes', 'MISSING')}'")
                            print(f"Retweets: '{tweet.get('retweets', 'MISSING')}'") 
                            print(f"Replies: '{tweet.get('replies', 'MISSING')}'")
                            print(f"Hashtags: '{tweet.get('hashtags', 'MISSING')}'")
                            print(f"Mentions: '{tweet.get('mentions', 'MISSING')}'")
                            print(f"Display Name: '{tweet.get('display_name', 'MISSING')}'")
                            print(f"Timestamp: '{tweet.get('timestamp', 'MISSING')}'")
                            
                            if i >= 2:  # Show first 3 tweets
                                break
                                
                        # Check if ANY tweet has engagement data
                        has_likes = any(tweet.get('likes', '0') != '0' for tweet in tweets)
                        has_hashtags = any(tweet.get('hashtags', '') != '' for tweet in tweets)
                        has_mentions = any(tweet.get('mentions', '') != '' for tweet in tweets)
                        
                        print(f"\\n🔍 ENGAGEMENT ANALYSIS:")
                        print(f"Has likes data: {'✅' if has_likes else '❌'}")
                        print(f"Has hashtags data: {'✅' if has_hashtags else '❌'}")
                        print(f"Has mentions data: {'✅' if has_mentions else '❌'}")
                        
                        if not has_likes:
                            print("\\n⚠️  ISSUE: No engagement metrics found!")
                        if not has_hashtags and not has_mentions:
                            print("⚠️  ISSUE: No hashtags or mentions extracted!")
                            
            except Exception as e:
                print(f"Error reading CSV: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("❌ FAILED: No file created")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()