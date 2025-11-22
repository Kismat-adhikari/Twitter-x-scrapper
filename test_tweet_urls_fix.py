"""
Test script to verify the tweet_urls parameter works correctly
"""
from scraper.playwright_scraper import TwitterScraper

def test_tweet_urls_param():
    print("🧪 TESTING tweet_urls PARAMETER FIX")
    print("=" * 50)
    
    scraper = TwitterScraper()
    
    # Test 1: Normal keyword search (should work)
    print("Test 1: Normal keyword search...")
    try:
        result = scraper.scrape(
            keyword="AI technology",
            num_tweets=5,
            job_id="test_normal"
        )
        print(f"✅ Normal search: {result}")
    except Exception as e:
        print(f"❌ Normal search failed: {e}")
    
    # Test 2: With tweet_urls parameter (should not crash)
    print("\nTest 2: With tweet_urls parameter...")
    try:
        result = scraper.scrape(
            keyword="python",
            tweet_urls=[],  # Empty list
            num_tweets=3,
            job_id="test_urls"
        )
        print(f"✅ tweet_urls parameter accepted: {result}")
    except Exception as e:
        print(f"❌ tweet_urls parameter failed: {e}")
    
    print("\n✅ Parameter compatibility test complete!")

if __name__ == "__main__":
    test_tweet_urls_param()