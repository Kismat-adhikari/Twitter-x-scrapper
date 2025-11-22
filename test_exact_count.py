"""
Test script to verify exact tweet count delivery with speed optimizations
"""
import time
from scraper.playwright_scraper import TwitterScraper

def test_exact_count():
    print("🧪 TESTING EXACT COUNT DELIVERY WITH SPEED OPTIMIZATIONS")
    print("=" * 60)
    
    # Test with 50 tweets (what user requested)
    target_tweets = 50
    search_query = "AI OR technology OR python"  # Broad search for good results
    
    print(f"🎯 Target: {target_tweets} tweets")
    print(f"🔍 Search: {search_query}")
    print(f"⏰ Starting at: {time.strftime('%H:%M:%S')}")
    print("-" * 40)
    
    start_time = time.time()
    
    # Initialize scraper with 8 parallel tabs
    scraper = TwitterScraper(num_tabs=8)
    
    # Run scraping
    result_file = scraper.scrape(
        keyword=search_query,
        num_tweets=target_tweets,
        job_id="exact_count_test"
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("📊 RESULTS:")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    print(f"📁 Output file: {result_file}")
    
    if result_file:
        # Count actual tweets in CSV
        import csv
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                actual_count = sum(1 for row in reader)
            
            print(f"🎯 Target tweets: {target_tweets}")
            print(f"✅ Actual tweets: {actual_count}")
            
            accuracy = (actual_count / target_tweets) * 100
            print(f"📈 Accuracy: {accuracy:.1f}%")
            
            tweets_per_second = actual_count / duration
            print(f"⚡ Speed: {tweets_per_second:.1f} tweets/second")
            
            if actual_count >= target_tweets * 0.9:  # 90% or better
                print("🏆 SUCCESS: Excellent accuracy!")
            elif actual_count >= target_tweets * 0.8:  # 80% or better
                print("✅ GOOD: Good accuracy!")
            else:
                print("⚠️  ATTENTION: Lower than expected count")
            
            if duration < 60:  # Under 1 minute
                print("🚀 SPEED: Excellent performance!")
            elif duration < 120:  # Under 2 minutes
                print("⚡ SPEED: Good performance!")
            else:
                print("⏳ SPEED: Could be faster")
                
        except Exception as e:
            print(f"❌ Error reading results: {e}")
    else:
        print("❌ No results file generated")

if __name__ == "__main__":
    test_exact_count()