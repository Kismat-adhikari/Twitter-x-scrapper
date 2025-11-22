"""
Test script to verify 100 tweet scraping works
Run this to test if the scraper can collect 100 tweets
"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime

def test_100_tweets():
    print("=" * 60)
    print("Testing 100 Tweet Scraping")
    print("=" * 60)
    
    # Create scraper
    scraper = TwitterScraper(num_tabs=4)
    
    # Test parameters
    keyword = "AI"
    num_tweets = 100
    job_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print(f"\n🎯 Target: {num_tweets} tweets")
    print(f"🔍 Keyword: {keyword}")
    print(f"📝 Job ID: {job_id}")
    print(f"🚀 Starting scrape...\n")
    
    try:
        # Run scraper
        filename = scraper.scrape(
            keyword=keyword,
            hashtag='',
            username='',
            tweet_url='',
            num_tweets=num_tweets,
            job_id=job_id
        )
        
        if filename:
            # Count tweets in CSV
            import csv
            csv_path = f'scraped_data/{filename}'
            
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                tweets = list(reader)
                actual_count = len(tweets)
            
            print("\n" + "=" * 60)
            print("RESULTS")
            print("=" * 60)
            print(f"✅ Target: {num_tweets} tweets")
            print(f"📊 Actual: {actual_count} tweets")
            print(f"📈 Success Rate: {(actual_count/num_tweets)*100:.1f}%")
            print(f"📁 File: {filename}")
            
            if actual_count >= num_tweets * 0.9:  # 90% or more
                print("\n🎉 SUCCESS! Got 90%+ of target tweets")
            elif actual_count >= num_tweets * 0.7:  # 70% or more
                print("\n⚠️  PARTIAL SUCCESS - Got 70%+ of target")
            else:
                print("\n❌ FAILED - Got less than 70% of target")
                print("\nPossible issues:")
                print("- Not enough tweets available for this keyword")
                print("- Twitter rate limiting")
                print("- Cookies expired")
                print("- Proxies not working")
            
            print("\n" + "=" * 60)
            
        else:
            print("\n❌ FAILED - No tweets collected")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_100_tweets()
