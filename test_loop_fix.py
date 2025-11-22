"""
Test script to verify the infinite loop fixes
"""
import time
from scraper.playwright_scraper import TwitterScraper

def test_loop_fix():
    print("🧪 TESTING INFINITE LOOP FIXES")
    print("=" * 50)
    
    # Test with a query that might have issues
    target_tweets = 10  # Small number for quick test
    search_query = "very_rare_query_12345"  # Intentionally difficult query
    
    print(f"🎯 Target: {target_tweets} tweets")
    print(f"🔍 Search: {search_query}")
    print(f"⏰ Starting at: {time.strftime('%H:%M:%S')}")
    print("🚨 This should exit gracefully even if no tweets found")
    print("-" * 40)
    
    start_time = time.time()
    
    # Initialize scraper
    scraper = TwitterScraper(num_tabs=2)  # Use fewer tabs for testing
    scraper.turbo_mode = False  # Force standard mode for testing
    
    # Run scraping with timeout
    try:
        result_file = scraper.scrape(
            keyword=search_query,
            num_tweets=target_tweets,
            job_id="loop_fix_test"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 50)
        print("📊 RESULTS:")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"📁 Output file: {result_file}")
        
        if duration < 60:  # Should not take more than 1 minute for this test
            print("✅ SUCCESS: No infinite loop detected!")
        else:
            print("⚠️  WARNING: Took longer than expected")
            
        if result_file:
            print("📈 Some tweets were collected")
        else:
            print("📉 No tweets collected (expected for rare query)")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_loop_fix()