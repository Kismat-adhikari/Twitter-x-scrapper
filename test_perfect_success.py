#!/usr/bin/env python3
"""
Perfect 100% Success Rate Test
Addresses the content exhaustion issue for 100% target achievement
"""

import os
import time
from datetime import datetime
from scraper.playwright_scraper import TwitterScraper

def test_perfect_success_rate():
    """Test to achieve 100% success rate by using smart strategies"""
    print("🎯 Testing PERFECT 100% Success Rate Optimization")
    print("=" * 60)
    
    target_tweets = 150
    
    # Create scraper with conservative but effective settings
    scraper = TwitterScraper(num_tabs=6)  # Optimal balance
    
    start_time = time.time()
    start_formatted = datetime.now().strftime("%H:%M:%S")
    
    print(f"⏰ Started at: {start_formatted}")
    print(f"🎯 Target: {target_tweets} tweets (PERFECT SUCCESS STRATEGY)")
    print(f"🔧 Strategy: Multiple query variations + extended patience")
    
    try:
        # Strategy 1: Use broader query for more content
        job_id = f"perfect_{target_tweets}_{datetime.now().strftime('%H%M%S')}"
        
        result_file = scraper.scrape(
            keyword='AI',  # Broader query = more content availability
            num_tweets=target_tweets,
            search_mode='live',  # Live mode has more content than top
            job_id=job_id
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Analyze results
        if result_file and os.path.exists(result_file):
            # Count actual tweets collected
            with open(result_file, 'r', encoding='utf-8') as f:
                line_count = sum(1 for line in f) - 1
            
            # Calculate success metrics
            success_rate = (line_count / target_tweets) * 100
            tweets_per_second = line_count / duration if duration > 0 else 0
            
            print("\n" + "=" * 60)
            print("🎯 PERFECT SUCCESS TEST RESULTS:")
            print(f"⏱️  Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
            print(f"📁 File: {os.path.basename(result_file)}")
            print(f"📊 Tweets collected: {line_count}/{target_tweets}")
            print(f"📈 Success rate: {success_rate:.1f}%")
            print(f"🚀 Speed: {tweets_per_second:.1f} tweets/second")
            
            if success_rate >= 95:
                print("🎉 PERFECT! Near 100% success rate achieved!")
            elif success_rate >= 90:
                print("✅ EXCELLENT! 90%+ success rate achieved!")
            elif success_rate >= 80:
                print("✅ VERY GOOD! 80%+ success rate achieved!")
            else:
                print(f"⚠️  NEEDS OPTIMIZATION: {success_rate:.1f}% success rate")
            
            # Strategy assessment
            if line_count < target_tweets:
                shortage = target_tweets - line_count
                print(f"\n📊 ANALYSIS:")
                print(f"Shortage: {shortage} tweets ({(shortage/target_tweets)*100:.1f}%)")
                print(f"Likely cause: Content exhaustion at tweet #{line_count}")
                
                # Provide solutions
                print(f"\n💡 SOLUTIONS FOR 100% SUCCESS:")
                print(f"1. 🔄 Query Rotation: Use multiple search terms")
                print(f"2. 🕒 Timing: Try different times of day")
                print(f"3. 📊 Mode Switch: Combine 'top' + 'live' modes")
                print(f"4. 🎯 Batch Strategy: {line_count} + {shortage} in second session")
            
            return line_count, target_tweets, success_rate
        else:
            print("❌ No result file generated")
            return 0, target_tweets, 0
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        return 0, target_tweets, 0

def test_dual_mode_strategy():
    """Advanced strategy: Combine TOP + LIVE modes for 100% success"""
    print("\n🎯 Testing DUAL MODE Strategy for 100% Success")
    print("=" * 60)
    
    target_tweets = 150
    
    # Strategy: Get 75 from TOP mode + 75 from LIVE mode
    scraper = TwitterScraper(num_tabs=6)
    
    print(f"🎯 Target: {target_tweets} tweets")
    print(f"📊 Strategy: 75 TOP mode + 75 LIVE mode")
    
    try:
        job_id = f"dual_mode_{datetime.now().strftime('%H%M%S')}"
        
        # First batch: TOP mode (popular tweets)
        print("\n🔥 Phase 1: Collecting TOP tweets...")
        result_file_1 = scraper.scrape(
            keyword='AI min_faves:10',  # Slightly higher threshold
            num_tweets=75,
            search_mode='top',
            job_id=f"{job_id}_top"
        )
        
        # Small delay
        time.sleep(5)
        
        # Second batch: LIVE mode (recent tweets)  
        print("\n⚡ Phase 2: Collecting LIVE tweets...")
        result_file_2 = scraper.scrape(
            keyword='AI',  # Broader for live mode
            num_tweets=75,
            search_mode='live',
            job_id=f"{job_id}_live"
        )
        
        # Analyze combined results
        total_collected = 0
        if result_file_1 and os.path.exists(result_file_1):
            with open(result_file_1, 'r', encoding='utf-8') as f:
                count_1 = sum(1 for line in f) - 1
            total_collected += count_1
            print(f"✅ Phase 1 collected: {count_1} tweets")
        
        if result_file_2 and os.path.exists(result_file_2):
            with open(result_file_2, 'r', encoding='utf-8') as f:
                count_2 = sum(1 for line in f) - 1
            total_collected += count_2
            print(f"✅ Phase 2 collected: {count_2} tweets")
        
        dual_success_rate = (total_collected / target_tweets) * 100
        
        print(f"\n🏆 DUAL MODE RESULTS:")
        print(f"📊 Total collected: {total_collected}/{target_tweets}")
        print(f"📈 Success rate: {dual_success_rate:.1f}%")
        
        if dual_success_rate >= 95:
            print("🎉 DUAL MODE SUCCESS! Near perfect collection!")
        
        return total_collected, target_tweets, dual_success_rate
        
    except Exception as e:
        print(f"❌ Error in dual mode: {e}")
        return 0, target_tweets, 0

if __name__ == "__main__":
    # Test 1: Single optimized approach
    collected_1, target_1, rate_1 = test_perfect_success_rate()
    
    # Test 2: Dual mode approach
    collected_2, target_2, rate_2 = test_dual_mode_strategy()
    
    # Final analysis
    print(f"\n🎯 FINAL COMPARISON:")
    print(f"Single Mode: {collected_1}/{target_1} ({rate_1:.1f}%)")
    print(f"Dual Mode: {collected_2}/{target_2} ({rate_2:.1f}%)")
    
    best_rate = max(rate_1, rate_2)
    if best_rate >= 95:
        print(f"🎉 SOLUTION FOUND! {best_rate:.1f}% success rate achieved!")
    else:
        print(f"📈 Best: {best_rate:.1f}% - Additional optimization needed")