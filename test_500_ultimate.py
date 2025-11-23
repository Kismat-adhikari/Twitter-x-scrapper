#!/usr/bin/env python3
"""
🧪 Test 500 tweet collection - Ultimate stress test
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.playwright_scraper import TwitterScraper

def test_500_tweets():
    """Test collecting 500 tweets - ultimate stress test"""
    print("🧪 Testing 500 tweet collection - ULTIMATE STRESS TEST")
    print("=" * 60)
    
    # Test parameters
    keyword = "AI"
    num_tweets = 500
    
    # Initialize scraper 
    scraper = TwitterScraper()
    # Disable broken proxies
    scraper.proxy_manager.proxies = []
    
    # Start timing
    start_time = time.time()
    print(f"⏰ Started at: {time.strftime('%H:%M:%S')}")
    print(f"🎯 Target: {num_tweets} tweets (ULTIMATE CHALLENGE!)")
    
    try:
        # Run scraping
        filename = scraper.scrape(
            keyword=keyword,
            num_tweets=num_tweets,
            job_id="test_500_ultimate",
            search_mode='top'
        )
        
        # Calculate time
        end_time = time.time()
        total_time = end_time - start_time
        minutes = total_time / 60
        
        print("=" * 60)
        print("🚀 500 TWEET ULTIMATE TEST RESULTS:")
        print(f"⏱️  Total time: {total_time:.1f} seconds ({minutes:.1f} minutes)")
        print(f"📁 File: {filename}")
        
        if filename:
            # Check results
            try:
                with open(f"scraped_data/{filename}", 'r', encoding='utf-8-sig') as f:
                    lines = f.readlines()
                    actual_count = len(lines) - 1  # Minus header
                
                success_rate = (actual_count / num_tweets) * 100
                print(f"📊 Tweets collected: {actual_count}/{num_tweets}")
                print(f"📈 Success rate: {success_rate:.1f}%")
                print(f"🚀 Speed: {actual_count/total_time:.1f} tweets/second")
                
                if actual_count >= 450:
                    print("🏆 OUTSTANDING! 90%+ collection rate for 500 tweets!")
                    print("🎉 Your scraper is ENTERPRISE-GRADE!")
                elif actual_count >= 400:
                    print("✅ EXCELLENT! 80%+ collection rate for massive target!")
                elif actual_count >= 350:
                    print("✅ VERY GOOD! 70%+ for such a large target!")
                elif actual_count >= 300:
                    print("⚠️  GOOD but room for improvement - 60%+ rate")
                else:
                    print("⚠️  NEEDS OPTIMIZATION for very large targets")
                
                # File size analysis
                file_size = os.path.getsize(f"scraped_data/{filename}")
                print(f"📏 File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
                
                # Show some high-engagement samples
                print(f"\n🔥 ENGAGEMENT ANALYSIS:")
                import csv
                with open(f"scraped_data/{filename}", 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    tweets = list(reader)
                    
                    high_engagement = [t for t in tweets if int(t.get('likes', 0)) >= 1000]
                    very_high = [t for t in tweets if int(t.get('likes', 0)) >= 10000]
                    
                    print(f"💥 High engagement (1K+ likes): {len(high_engagement)}")
                    print(f"🔥 Very high engagement (10K+ likes): {len(very_high)}")
                    
                    # Show top 3 by likes
                    sorted_tweets = sorted(tweets, key=lambda x: int(x.get('likes', 0)), reverse=True)
                    print(f"\n🏆 TOP 3 BY ENGAGEMENT:")
                    for i, tweet in enumerate(sorted_tweets[:3]):
                        likes = tweet.get('likes', 0)
                        username = tweet.get('username', 'unknown')
                        text = tweet.get('text', 'No text')[:60] + "..."
                        print(f"  {i+1}. @{username}: {likes:,} likes")
                        print(f"      {text}")
                        
            except Exception as e:
                print(f"⚠️  Could not analyze file: {e}")
        else:
            print("❌ No file created - optimization needed for 500 tweets")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_500_tweets()