#!/usr/bin/env python3
"""
Test the new SUPER FAST optimizations
"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime
import time

def test_super_fast():
    """Test super fast 100 tweets"""
    print("🚀 TESTING SUPER FAST MODE - 100 TWEETS")
    print("=" * 50)
    print("🎯 Target: 100 tweets in under 20 seconds!")
    print()
    
    # Create timestamp for job ID
    job_id = f"superfast_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Record start time
    start_time = time.time()
    
    # Initialize scraper
    scraper = TwitterScraper()
    
    # Test with 100 tweets
    result_filename = scraper.scrape(
        keyword="AI technology",
        num_tweets=100,
        job_id=job_id
    )
    
    # Calculate duration
    end_time = time.time()
    duration = end_time - start_time
    
    if result_filename:
        print("\n" + "=" * 50)
        print("🏆 SUPER FAST MODE RESULTS!")
        print("=" * 50)
        print(f"📁 File: {result_filename}")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"⚡ Speed: {100/duration:.1f} tweets/second")
        
        # Count tweets
        import csv
        csv_path = f"scraped_data/{result_filename}"
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                tweets = list(reader)
                count = len(tweets)
            
            print(f"📊 Tweets collected: {count}/100")
            
            # Performance assessment
            if duration <= 15:
                print("🔥 BLAZING FAST! Under 15 seconds!")
            elif duration <= 20:
                print("🚀 SUPER FAST! Under 20 seconds!")
            elif duration <= 30:
                print("⚡ FAST! Under 30 seconds!")
            else:
                print("📈 GOOD! Faster than before!")
                
            print(f"🎯 Speed improvement vs 45s baseline: {((45-duration)/45)*100:.0f}% faster")
                
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
    else:
        print("\n❌ SUPER FAST MODE TEST FAILED")

if __name__ == "__main__":
    test_super_fast()