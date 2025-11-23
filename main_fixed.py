#!/usr/bin/env python3
"""
🔧 FIXED Twitter Scraper - Works without broken proxies
"""

from scraper.playwright_scraper import TwitterScraper
import os
from datetime import datetime

def get_user_input():
    """Get scraping parameters from user"""
    print("🐦 Twitter/X Scraper - FIXED VERSION")
    print("=" * 50)
    
    # Get keyword
    print("💡 Tip: You can use multiple keywords, quotes for exact phrases")
    print("   Examples: 'AI technology', '\"machine learning\" AI', 'crypto bitcoin'")
    keyword = input("Enter keyword(s) to search (or press Enter to skip): ").strip()
    
    # Get hashtag
    hashtag = input("Enter hashtag to search (without #, or press Enter to skip): ").strip()
    
    # Get username
    username = input("Enter username to search (without @, or press Enter to skip): ").strip()
    if username and not username.startswith('@'):
        username = f"@{username}"
    
    # Validate at least one search parameter
    if not keyword and not hashtag and not username:
        print("❌ Error: You must provide at least one search parameter!")
        return None
    
    # Always use TOP mode
    search_mode = 'top'
    print("\n📊 Mode: TOP (Popular tweets with high engagement)")
    
    # Get number of tweets
    while True:
        try:
            num_tweets = int(input("\nEnter number of tweets to scrape (10-500): ").strip())
            if 10 <= num_tweets <= 500:
                break
            else:
                print("❌ Please enter a number between 10 and 500")
        except ValueError:
            print("❌ Please enter a valid number")
    
    return {
        'keyword': keyword if keyword else '',
        'hashtag': hashtag if hashtag else '',
        'username': username if username else '',
        'num_tweets': num_tweets,
        'search_mode': search_mode
    }

def main():
    """Main scraper function - FIXED VERSION"""
    try:
        # Get user input
        params = get_user_input()
        if not params:
            return
        
        print(f"\n🔍 Searching for:")
        if params['keyword']:
            print(f"  Keywords: {params['keyword']}")
        if params['hashtag']:
            print(f"  Hashtag: #{params['hashtag']}")
        if params['username']:
            print(f"  Username: {params['username']}")
        print(f"  Target: {params['num_tweets']} tweets")
        
        # Confirm before starting
        confirm = input("\nStart scraping? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ Scraping cancelled")
            return
        
        print("\n🚀 Starting scraper (WITHOUT BROKEN PROXIES)...")
        print("=" * 50)
        
        # Create timestamp for job ID
        job_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Initialize scraper and DISABLE BROKEN PROXIES
        scraper = TwitterScraper()
        
        # DISABLE BROKEN PROXIES - Use direct connection which works
        print("⚠️  Disabling broken proxies, using direct connection...")
        scraper.proxy_manager.proxies = []  # Clear broken proxy list
        
        # Start scraping
        result_filename = scraper.scrape(
            keyword=params['keyword'],
            hashtag=params['hashtag'],
            username=params['username'],
            num_tweets=params['num_tweets'],
            job_id=job_id,
            search_mode=params.get('search_mode', 'top')
        )
        
        if result_filename:
            print("\n" + "=" * 50)
            print("✅ SCRAPING COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            print(f"📁 File saved: {result_filename}")
            
            # Show file info
            csv_path = f"scraped_data/{result_filename}"
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, 'r', encoding='utf-8-sig') as f:
                        lines = f.readlines()
                        actual_count = len(lines) - 1  # Minus header
                    
                    file_size = os.path.getsize(csv_path)
                    print(f"📊 Tweets collected: {actual_count}")
                    print(f"📏 File size: {file_size:,} bytes")
                    print(f"📂 Full path: {os.path.abspath(csv_path)}")
                    
                    # Show first few tweets as preview
                    if actual_count > 0:
                        print(f"\n📋 Preview of collected tweets:")
                        print("-" * 40)
                        
                        import csv
                        with open(csv_path, 'r', encoding='utf-8-sig') as f:
                            reader = csv.DictReader(f)
                            for i, row in enumerate(reader):
                                if i >= 3:  # Show first 3 tweets
                                    break
                                text = row.get('text', 'No text')[:80] + "..." if len(row.get('text', '')) > 80 else row.get('text', 'No text')
                                username = row.get('username', 'Unknown')
                                likes = row.get('likes', '0')
                                print(f"  {i+1}. @{username}: {text}")
                                print(f"     💖 {likes} likes")
                        
                        if actual_count > 3:
                            print(f"  ... and {actual_count - 3} more tweets")
                        
                        print(f"\n🎉 SUCCESS! Your scraper is working - the issue was broken proxies!")
                        
                except Exception as e:
                    print(f"⚠️  Could not read file details: {e}")
            
        else:
            print("\n" + "=" * 50)
            print("❌ SCRAPING FAILED")
            print("=" * 50)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()