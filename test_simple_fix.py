from scraper.playwright_scraper import TwitterScraper
import time

def test_quick_search():
    """Test with a simple, popular keyword"""
    scraper = TwitterScraper()
    
    print("🧪 QUICK TEST: Simple keyword search")
    print("=" * 50)
    
    start_time = time.time()
    
    try:
        # Use a very popular, simple keyword
        keyword = "news"
        hashtag = ""
        username = ""
        num_tweets = 20  # Small test
        
        print(f"🔍 Testing with keyword: '{keyword}'")
        print(f"🎯 Target: {num_tweets} tweets")
        
        url = scraper.build_url(keyword, hashtag, username, "")
        print(f"🔗 URL: {url}")
        print()
        
        job_id = scraper.scrape(
            keyword=keyword,
            hashtag=hashtag,  
            username=username,
            num_tweets=num_tweets
        )
        
        duration = time.time() - start_time
        print(f"\n✅ Test completed in {duration:.1f} seconds")
        print(f"📁 Job ID: {job_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_quick_search()