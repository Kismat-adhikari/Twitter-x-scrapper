#!/usr/bin/env python3
"""
Test script to verify real engagement metrics are being extracted
"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime
import csv
import os

def test_engagement_extraction():
    """Test that engagement metrics are real (not 0)"""
    print("🧪 Testing Real Engagement Extraction")
    print("=" * 60)
    
    # Check if cookies exist
    if not os.path.exists('x.com_cookies.txt'):
        print("⚠️  WARNING: x.com_cookies.txt not found!")
        print("   The scraper needs cookies to extract real engagement.")
        print("   See REAL_ENGAGEMENT_FIX.md for setup instructions.")
        print()
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            return
    else:
        print("✅ Found x.com_cookies.txt")
    
    # Test parameters
    keyword = "AI"
    num_tweets = 10
    search_mode = "top"
    
    print(f"\n📋 Test Configuration:")
    print(f"  Keyword: {keyword}")
    print(f"  Mode: {search_mode.upper()}")
    print(f"  Target: {num_tweets} tweets")
    print()
    
    # Run scraper
    print("🚀 Starting scraper...")
    print("-" * 60)
    
    job_id = f"test_engagement_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    scraper = TwitterScraper(num_tabs=2)  # Use 2 tabs for faster testing
    
    result_filename = scraper.scrape(
        keyword=keyword,
        num_tweets=num_tweets,
        job_id=job_id,
        search_mode=search_mode
    )
    
    if not result_filename:
        print("\n❌ FAILED: No tweets collected")
        return
    
    # Analyze results
    print("\n" + "=" * 60)
    print("📊 ANALYZING RESULTS")
    print("=" * 60)
    
    csv_path = f"scraped_data/{result_filename}"
    
    if not os.path.exists(csv_path):
        print(f"❌ FAILED: CSV file not found: {csv_path}")
        return
    
    # Read and analyze CSV
    tweets_with_engagement = 0
    tweets_without_engagement = 0
    total_likes = 0
    total_retweets = 0
    total_replies = 0
    total_quotes = 0
    total_bookmarks = 0
    
    tweets_data = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                likes = int(row.get('likes', 0))
                retweets = int(row.get('retweets', 0))
                replies = int(row.get('replies', 0))
                quotes = int(row.get('quotes', 0))
                bookmarks = int(row.get('bookmarks', 0))
                
                total_likes += likes
                total_retweets += retweets
                total_replies += replies
                total_quotes += quotes
                total_bookmarks += bookmarks
                
                if likes > 0 or retweets > 0 or replies > 0:
                    tweets_with_engagement += 1
                else:
                    tweets_without_engagement += 1
                
                tweets_data.append({
                    'username': row.get('username', 'unknown'),
                    'text': row.get('text', '')[:60] + '...',
                    'likes': likes,
                    'retweets': retweets,
                    'replies': replies,
                    'quotes': quotes,
                    'bookmarks': bookmarks
                })
            except ValueError:
                continue
    
    total_tweets = tweets_with_engagement + tweets_without_engagement
    
    # Display results
    print(f"\n📈 Engagement Statistics:")
    print(f"  Total tweets: {total_tweets}")
    print(f"  Tweets WITH engagement: {tweets_with_engagement} ({tweets_with_engagement/total_tweets*100:.1f}%)")
    print(f"  Tweets WITHOUT engagement: {tweets_without_engagement} ({tweets_without_engagement/total_tweets*100:.1f}%)")
    print()
    print(f"  Average likes: {total_likes/total_tweets:.1f}")
    print(f"  Average retweets: {total_retweets/total_tweets:.1f}")
    print(f"  Average replies: {total_replies/total_tweets:.1f}")
    print(f"  Average quotes: {total_quotes/total_tweets:.1f}")
    print(f"  Average bookmarks: {total_bookmarks/total_tweets:.1f}")
    
    # Show sample tweets
    print(f"\n📋 Sample Tweets:")
    print("-" * 60)
    for i, tweet in enumerate(tweets_data[:5], 1):
        print(f"{i}. @{tweet['username']}")
        print(f"   {tweet['text']}")
        print(f"   💙 {tweet['likes']} | 🔄 {tweet['retweets']} | 💬 {tweet['replies']} | 💭 {tweet['quotes']} | 🔖 {tweet['bookmarks']}")
        print()
    
    # Verdict
    print("=" * 60)
    print("🎯 TEST VERDICT")
    print("=" * 60)
    
    if tweets_with_engagement == 0:
        print("❌ FAILED: All tweets have 0 engagement")
        print()
        print("Possible issues:")
        print("  1. Cookies are missing or expired")
        print("  2. API interception is not working")
        print("  3. Twitter changed their API structure")
        print()
        print("Solutions:")
        print("  1. Update x.com_cookies.txt with fresh cookies")
        print("  2. Check that you're logged in to Twitter")
        print("  3. See REAL_ENGAGEMENT_FIX.md for troubleshooting")
    elif tweets_with_engagement < total_tweets * 0.5:
        print("⚠️  PARTIAL: Some tweets have engagement, but many don't")
        print()
        print(f"  {tweets_with_engagement}/{total_tweets} tweets have engagement")
        print()
        print("This might be normal if:")
        print("  - Some tweets are very new")
        print("  - API interception is working partially")
        print()
        print("Consider:")
        print("  - Using TOP mode (already selected)")
        print("  - Refreshing your cookies")
    else:
        print("✅ SUCCESS: Most tweets have real engagement!")
        print()
        print(f"  {tweets_with_engagement}/{total_tweets} tweets have engagement")
        print(f"  Average engagement: {(total_likes + total_retweets + total_replies)/total_tweets:.1f}")
        print()
        print("🎉 The scraper is working correctly!")
        print("   Real engagement metrics are being extracted from Twitter's API.")
    
    print()
    print(f"📁 Full results saved to: {csv_path}")

if __name__ == "__main__":
    try:
        test_engagement_extraction()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
