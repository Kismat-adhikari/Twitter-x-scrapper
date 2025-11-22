#!/usr/bin/env python3
"""
Twitter/X Scraper - Terminal Interface
Clean backend-only implementation
"""

from scraper.playwright_scraper import TwitterScraper
import os
from datetime import datetime

def get_user_input():
    """Get scraping parameters from user"""
    print("🐦 Twitter/X Scraper - Terminal Edition")
    print("=" * 50)
    
    # Get keyword
    print("💡 Tip: You can use multiple keywords, quotes for exact phrases")
    print("   Examples: 'AI technology', '\"machine learning\" AI', 'crypto bitcoin'")
    keyword = input("Enter keyword(s) to search (or press Enter to skip): ").strip()
    
    # Get hashtag
    hashtag = input("Enter hashtag to search (without #, or press Enter to skip): ").strip()
    # Don't add # here - let the scraper handle it
    
    # Get username
    username = input("Enter username to search (without @, or press Enter to skip): ").strip()
    if username and not username.startswith('@'):
        username = f"@{username}"
    
    # Validate at least one search parameter
    if not keyword and not hashtag and not username:
        print("❌ Error: You must provide at least one search parameter!")
        return None
    
    # Get number of tweets
    while True:
        try:
            num_tweets = int(input("Enter number of tweets to scrape (10-500): ").strip())
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
        'num_tweets': num_tweets
    }

def display_search_info(params):
    """Display what will be searched"""
    print("\n📋 Search Configuration:")
    print("-" * 30)
    
    search_terms = []
    if params['keyword']:
        # Show individual keywords if multiple
        keywords_display = f"Keywords: '{params['keyword']}'"
        if ' ' in params['keyword'] and '"' not in params['keyword']:
            keywords_display += f" (multiple terms)"
        search_terms.append(keywords_display)
    if params['hashtag']:
        # Display hashtags with # prefix for clarity, even though we don't store them with #
        hashtag_display = params['hashtag']
        if not hashtag_display.startswith('#'):
            if ',' in hashtag_display:
                # Multiple hashtags
                hashtags = [f"#{tag.strip()}" for tag in hashtag_display.split(',') if tag.strip()]
                hashtag_display = ', '.join(hashtags)
            else:
                hashtag_display = f"#{hashtag_display}"
        search_terms.append(f"Hashtag: '{hashtag_display}'")
    if params['username']:
        search_terms.append(f"Username: '{params['username']}'")
    
    for term in search_terms:
        print(f"  🔍 {term}")
    
    print(f"  🎯 Target: {params['num_tweets']} tweets")
    
    # Determine mode
    if params['num_tweets'] >= 50:
        print(f"  🚀 Mode: TURBO MODE (FastCSVHandler)")
    else:
        print(f"  📝 Mode: STANDARD MODE (CSVHandler)")
    
    print()

def main():
    """Main scraper function"""
    try:
        # Get user input
        params = get_user_input()
        if not params:
            return
        
        # Display search info
        display_search_info(params)
        
        # Confirm before starting
        confirm = input("Start scraping? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("❌ Scraping cancelled")
            return
        
        print("\n🚀 Starting scraper...")
        print("=" * 50)
        
        # Create timestamp for job ID
        job_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Initialize scraper
        scraper = TwitterScraper()
        
        # Start scraping
        result_filename = scraper.scrape(
            keyword=params['keyword'],
            hashtag=params['hashtag'],
            username=params['username'],
            num_tweets=params['num_tweets'],
            job_id=job_id
        )
        
        if result_filename:
            print("\n" + "=" * 50)
            print("✅ SCRAPING COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            print(f"📁 File saved: {result_filename}")
            
            # Show file info
            csv_path = f"scraped_data/{result_filename}"
            if os.path.exists(csv_path):
                # Count actual tweets in file
                try:
                    with open(csv_path, 'r', encoding='utf-8-sig') as f:
                        lines = f.readlines()
                        actual_count = len(lines) - 1  # Minus header
                    
                    file_size = os.path.getsize(csv_path)
                    print(f"📊 Tweets collected: {actual_count}")
                    print(f"📏 File size: {file_size:,} bytes")
                    print(f"📂 Full path: {os.path.abspath(csv_path)}")
                    
                    # Show first few tweets as preview
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
                            print(f"  {i+1}. @{username}: {text}")
                    
                    if actual_count > 3:
                        print(f"  ... and {actual_count - 3} more tweets")
                    
                except Exception as e:
                    print(f"⚠️  Could not read file details: {e}")
            
        else:
            print("\n" + "=" * 50)
            print("❌ SCRAPING FAILED")
            print("=" * 50)
            print("No tweets were collected. This might be due to:")
            print("  • Network connection issues")
            print("  • Search terms too specific")
            print("  • Twitter rate limiting")
            print("  • Browser automation detection")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()