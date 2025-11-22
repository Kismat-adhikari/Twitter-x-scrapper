#!/usr/bin/env python3
"""
Test script to compare different search modes and their engagement levels
"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime
import csv

def test_mode(mode_name, search_mode, keyword, num_tweets=20):
    """Test a specific search mode"""
    print(f"\n{'='*60}")
    print(f"Testing {mode_name} Mode")
    print(f"{'='*60}")
    
    job_id = f"test_{mode_name.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    scraper = TwitterScraper(num_tabs=2)  # Use 2 tabs for faster testing
    
    result_filename = scraper.scrape(
        keyword=keyword,
        num_tweets=num_tweets,
        job_id=job_id,
        search_mode=search_mode
    )
    
    if result_filename:
        csv_path = f"scraped_data/{result_filename}"
        
        # Analyze engagement
        total_likes = 0
        total_retweets = 0
        total_replies = 0
        tweets_with_engagement = 0
        tweets_without_engagement = 0
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                likes = int(row.get('likes', 0))
                retweets = int(row.get('retweets', 0))
                replies = int(row.get('replies', 0))
                
                total_likes += likes
                total_retweets += retweets
                total_replies += replies
                
                if likes > 0 or retweets > 0 or replies > 0:
                    tweets_with_engagement += 1
                else:
                    tweets_without_engagement += 1
        
        total_tweets = tweets_with_engagement + tweets_without_engagement
        
        print(f"\n📊 Results for {mode_name} Mode:")
        print(f"  Total tweets: {total_tweets}")
        print(f"  Tweets WITH engagement: {tweets_with_engagement} ({tweets_with_engagement/total_tweets*100:.1f}%)")
        print(f"  Tweets WITHOUT engagement: {tweets_without_engagement} ({tweets_without_engagement/total_tweets*100:.1f}%)")
        print(f"  Average likes per tweet: {total_likes/total_tweets:.1f}")
        print(f"  Average retweets per tweet: {total_retweets/total_tweets:.1f}")
        print(f"  Average replies per tweet: {total_replies/total_tweets:.1f}")
        
        return {
            'mode': mode_name,
            'total': total_tweets,
            'with_engagement': tweets_with_engagement,
            'without_engagement': tweets_without_engagement,
            'avg_likes': total_likes/total_tweets if total_tweets > 0 else 0,
            'avg_retweets': total_retweets/total_tweets if total_tweets > 0 else 0,
            'avg_replies': total_replies/total_tweets if total_tweets > 0 else 0
        }
    else:
        print(f"❌ Failed to scrape tweets in {mode_name} mode")
        return None

def main():
    """Compare all three modes"""
    print("🧪 Testing Engagement Filtering Modes")
    print("This will scrape 20 tweets in each mode and compare engagement levels")
    
    keyword = input("\nEnter a keyword to test (e.g., 'AI', 'crypto', 'technology'): ").strip()
    if not keyword:
        keyword = "AI"
        print(f"Using default keyword: {keyword}")
    
    num_tweets = 20
    
    results = []
    
    # Test TOP mode
    result = test_mode("TOP", "top", keyword, num_tweets)
    if result:
        results.append(result)
    
    # Test LIVE mode
    result = test_mode("LIVE", "live", keyword, num_tweets)
    if result:
        results.append(result)
    
    # Test PEOPLE mode
    result = test_mode("PEOPLE", "people", keyword, num_tweets)
    if result:
        results.append(result)
    
    # Summary comparison
    if results:
        print(f"\n{'='*60}")
        print("📊 COMPARISON SUMMARY")
        print(f"{'='*60}")
        print(f"\n{'Mode':<10} {'With Eng.':<12} {'Without Eng.':<14} {'Avg Likes':<12} {'Avg RTs':<12}")
        print("-" * 60)
        
        for r in results:
            print(f"{r['mode']:<10} {r['with_engagement']:<12} {r['without_engagement']:<14} {r['avg_likes']:<12.1f} {r['avg_retweets']:<12.1f}")
        
        print("\n💡 Recommendation:")
        best_mode = max(results, key=lambda x: x['with_engagement'])
        print(f"   Use {best_mode['mode']} mode for best engagement results!")
        print(f"   {best_mode['with_engagement']}/{best_mode['total']} tweets had engagement")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
