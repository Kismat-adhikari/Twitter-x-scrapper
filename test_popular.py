#!/usr/bin/env python3
"""
Quick test with popular keyword
"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime
import time

def test_popular_keyword():
    """Test with popular keyword"""
    print("🚀 TESTING WITH POPULAR KEYWORD - 100 TWEETS")
    print("=" * 50)
    
    # Create timestamp for job ID
    job_id = f"popular_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Record start time
    start_time = time.time()
    
    # Initialize scraper
    scraper = TwitterScraper()
    
    # Test with popular keyword that should have lots of content
    result_filename = scraper.scrape(
        keyword="breaking news",  # Very popular, lots of content
        num_tweets=100,
        job_id=job_id
    )
    
    # Calculate duration
    end_time = time.time()
    duration = end_time - start_time
    
    if result_filename:
        print("\n" + "=" * 50)
        print("🏆 POPULAR KEYWORD TEST RESULTS!")
        print("=" * 50)
        print(f"📁 File: {result_filename}")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"⚡ Speed: {100/duration:.1f} tweets/second")
        
        # Performance assessment
        if duration <= 20:
            print("🚀 EXCELLENT! Under 20 seconds!")
        elif duration <= 30:
            print("⚡ VERY GOOD! Under 30 seconds!")
        elif duration <= 45:
            print("📈 GOOD! Same as or better than baseline!")
        else:
            print("🤔 Slower than expected - might be network/content issues")

if __name__ == "__main__":
    test_popular_keyword()