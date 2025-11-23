#!/usr/bin/env python3
"""
500 Tweet Collection Test - OPTIMIZED VERSION
Enhanced scraper for very large targets with advanced strategies
"""

import os
import sys
import time
from datetime import datetime

from scraper.playwright_scraper import TwitterScraper

def test_500_tweets_optimized():
    """Test collecting 500 tweets with optimized strategies"""
    print("🚀 Testing OPTIMIZED 500 tweet collection")
    print("=" * 60)
    
    # Create scraper with maximum tabs
    scraper = TwitterScraper(num_tabs=12)
    
    start_time = time.time()
    start_formatted = datetime.now().strftime("%H:%M:%S")
    
    print(f"⏰ Started at: {start_formatted}")
    print(f"🎯 Target: 500 tweets (OPTIMIZED APPROACH)")
    print(f"🔧 Using optimized scraping method")
    
    try:
        # Enhanced scraping with optimization
        result_file = scraper.scrape_optimized(
            keyword='AI min_faves:1',
            num_tweets=500,
            search_mode='top'
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Analyze results
        if result_file and os.path.exists(result_file):
            # Count lines in CSV (subtract 1 for header)
            with open(result_file, 'r', encoding='utf-8') as f:
                line_count = sum(1 for line in f) - 1
            
            # Calculate performance metrics
            success_rate = (line_count / 500) * 100
            tweets_per_second = line_count / duration if duration > 0 else 0
            
            print("\n" + "=" * 60)
            print("🎯 OPTIMIZED 500 TWEET TEST RESULTS:")
            print(f"⏱️  Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            print(f"📁 File: {os.path.basename(result_file)}")
            print(f"📊 Tweets collected: {line_count}/500")
            print(f"📈 Success rate: {success_rate:.1f}%")
            print(f"🚀 Speed: {tweets_per_second:.1f} tweets/second")
            
            if success_rate >= 80:
                print("✅ EXCELLENT: Optimized approach works great for 500 tweets!")
            elif success_rate >= 50:
                print("✅ GOOD: Substantial improvement with optimization")
            elif success_rate > 30:
                print("⚠️  IMPROVED: Better than basic approach but needs more optimization")
            else:
                print("❌ CHALLENGE: Very large targets may need enterprise-grade solutions")
            
            # File size analysis
            file_size = os.path.getsize(result_file)
            print(f"📏 File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            return line_count
        else:
            print("❌ No result file generated")
            return 0
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        return 0

if __name__ == "__main__":
    result_count = test_500_tweets_optimized()
    print(f"\n🏁 Final result: {result_count} tweets collected")