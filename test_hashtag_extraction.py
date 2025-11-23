#!/usr/bin/env python3
"""
🧪 Test hashtag and mentions extraction
"""

import time
import sys
import os
import csv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.playwright_scraper import TwitterScraper

def test_hashtag_extraction():
    """Test hashtag and mentions extraction with crypto hashtags"""
    print("🧪 Testing hashtag extraction with #bitcoin search")
    print("=" * 50)
    
    # Test parameters - use hashtag to ensure we get hashtag-rich tweets
    hashtag = "bitcoin"
    num_tweets = 15
    
    # Initialize scraper
    scraper = TwitterScraper()
    scraper.turbo_mode = False  # Force standard mode
    
    # Start timing
    start_time = time.time()
    print(f"⏰ Started at: {time.strftime('%H:%M:%S')}")
    
    try:
        # Run scraping
        filename = scraper.scrape(
            hashtag=hashtag,
            num_tweets=num_tweets,
            job_id="hashtag_test",
            search_mode='top'
        )
        
        # Calculate time
        end_time = time.time()
        total_time = end_time - start_time
        
        print("=" * 50)
        print("📊 HASHTAG EXTRACTION TEST RESULTS:")
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"📁 File: {filename}")
        
        if filename:
            # Read and analyze CSV content
            try:
                tweets_with_hashtags = 0
                tweets_with_mentions = 0
                total_tweets = 0
                
                with open(f"scraped_data/{filename}", 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for i, row in enumerate(reader):
                        total_tweets += 1
                        text = row.get('text', '')
                        username = row.get('username', '')
                        likes = row.get('likes', '0')
                        hashtags = row.get('hashtags', '')
                        mentions = row.get('mentions', '')
                        
                        if hashtags:
                            tweets_with_hashtags += 1
                        if mentions:
                            tweets_with_mentions += 1
                        
                        # Show first 5 tweets with details
                        if i < 5:
                            print(f"\n--- Tweet {i+1} ---")
                            print(f"@{username}: {text[:80]}...")
                            print(f"💖 {likes} likes")
                            print(f"🏷️  Hashtags: {hashtags or 'None'}")
                            print(f"👥 Mentions: {mentions or 'None'}")
                
                print("\n" + "=" * 50)
                print("📊 EXTRACTION ANALYSIS:")
                print(f"📋 Total tweets: {total_tweets}")
                print(f"🏷️  Tweets with hashtags: {tweets_with_hashtags} ({tweets_with_hashtags/total_tweets*100:.1f}%)")
                print(f"👥 Tweets with mentions: {tweets_with_mentions} ({tweets_with_mentions/total_tweets*100:.1f}%)")
                
                if tweets_with_hashtags > 0:
                    print("✅ Hashtag extraction working!")
                else:
                    print("❌ No hashtags extracted - needs fixing")
                
                if tweets_with_mentions > 0:
                    print("✅ Mention extraction working!")
                else:
                    print("⚠️  No mentions found (could be normal)")
                    
            except Exception as e:
                print(f"⚠️  Could not analyze file: {e}")
        else:
            print("❌ No file created")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hashtag_extraction()