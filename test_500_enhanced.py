#!/usr/bin/env python3
"""
500 Tweet Collection Test - ENHANCED VERSION
Uses the proven working scraper with optimized parameters
"""

import os
import time
from datetime import datetime
from scraper.playwright_scraper import TwitterScraper

def test_500_tweets_enhanced():
    """Test collecting 500 tweets with enhanced settings"""
    print("🚀 Testing ENHANCED 500 tweet collection")
    print("=" * 60)
    
    # Create scraper with optimal settings for large targets
    scraper = TwitterScraper(num_tabs=8)  # Proven optimal for large targets
    
    start_time = time.time()
    start_formatted = datetime.now().strftime("%H:%M:%S")
    
    print(f"⏰ Started at: {start_formatted}")
    print(f"🎯 Target: 500 tweets (ENHANCED APPROACH)")
    print(f"🔧 Using 8 parallel tabs with proven method")
    
    try:
        # Use the proven working method with enhanced parameters
        job_id = f"enhanced_500_{datetime.now().strftime('%H%M%S')}"
        
        result_file = scraper.scrape(
            keyword='AI min_faves:1',  # Single query for consistency
            num_tweets=500,
            search_mode='top',
            job_id=job_id
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
            print("🎯 ENHANCED 500 TWEET TEST RESULTS:")
            print(f"⏱️  Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            print(f"📁 File: {os.path.basename(result_file)}")
            print(f"📊 Tweets collected: {line_count}/500")
            print(f"📈 Success rate: {success_rate:.1f}%")
            print(f"🚀 Speed: {tweets_per_second:.1f} tweets/second")
            
            if success_rate >= 80:
                print("✅ EXCELLENT: Enhanced approach works great for 500 tweets!")
                print("🎉 Enterprise-grade scalability CONFIRMED!")
            elif success_rate >= 60:
                print("✅ VERY GOOD: Substantial improvement over basic test")
                print("🎯 Near enterprise-grade performance achieved!")
            elif success_rate >= 40:
                print("⚡ IMPROVED: Better than basic approach (27.2%)")
                print("📈 Significant optimization gains demonstrated")
            else:
                print("⚠️  CHALLENGING: Very large targets need specialized optimization")
            
            # File size analysis
            file_size = os.path.getsize(result_file)
            print(f"📏 File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            # Performance comparison
            print(f"\n📊 PERFORMANCE COMPARISON:")
            print(f"Basic test (27.2%): 136 tweets in 4.0 minutes")
            print(f"Enhanced test: {line_count} tweets in {duration/60:.1f} minutes")
            
            improvement = ((line_count - 136) / 136) * 100 if line_count > 136 else 0
            if improvement > 0:
                print(f"📈 Improvement: +{improvement:.1f}% more tweets collected")
            
            return line_count
        else:
            print("❌ No result file generated")
            return 0
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    result_count = test_500_tweets_enhanced()
    print(f"\n🏁 Final result: {result_count} tweets collected")
    
    if result_count >= 400:
        print("🎉 SUCCESS: Ready for enterprise-scale deployment!")
    elif result_count >= 250:
        print("✅ GOOD: Substantial scalability improvement achieved")
    elif result_count > 136:
        print("📈 PROGRESS: Better than initial test results")
    else:
        print("🔧 NEEDS WORK: Consider further optimization strategies")