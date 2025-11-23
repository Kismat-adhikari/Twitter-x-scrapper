#!/usr/bin/env python3
"""
🧪 Simple test with very basic search terms
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.playwright_scraper import TwitterScraper

def test_simple_search():
    """Test with very simple search terms to avoid URL issues"""
    print("🧪 Testing with simple search terms")
    print("=" * 50)
    
    # Use very simple search terms
    keyword = "AI"  # Single keyword
    num_tweets = 5  # Small number
    
    # Initialize scraper
    scraper = TwitterScraper()
    
    # Start timing
    start_time = time.time()
    print(f"⏰ Started at: {time.strftime('%H:%M:%S')}")
    
    try:
        # Run scraping with simple terms
        filename = scraper.scrape(
            keyword=keyword,
            num_tweets=num_tweets,
            job_id="simple_search_test",
            search_mode='top'
        )
        
        # Calculate time
        end_time = time.time()
        total_time = end_time - start_time
        
        print("=" * 50)
        print("📊 SIMPLE SEARCH TEST RESULTS:")
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
                    print("✅ Simple search test successful!")
                    # Show a sample tweet
                    if len(lines) > 1:
                        import csv
                        import io
                        reader = csv.DictReader(io.StringIO(''.join(lines)))
                        for i, row in enumerate(reader):
                            if i < 2:  # Show first tweet
                                print(f"\nSample tweet:")
                                print(f"  👤 @{row.get('username', 'unknown')}")
                                print(f"  💬 {row.get('text', 'No text')[:100]}...")
                                print(f"  💖 {row.get('likes', 0)} likes")
                                break
                else:
                    print("❌ No tweets in file - likely all proxies failed or URLs are bad")
            except Exception as e:
                print(f"⚠️  Could not read file: {e}")
        else:
            print("❌ No file created - all tabs likely failed")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_search()