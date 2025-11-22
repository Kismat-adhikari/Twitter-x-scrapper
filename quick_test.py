#!/usr/bin/env python3
"""
Quick test of the terminal scraper with TURBO MODE
"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime

def quick_turbo_test():
    """Test TURBO MODE with 50 tweets"""
    print("🧪 Testing TURBO MODE (50 tweets)")
    print("=" * 40)
    
    # Create timestamp for job ID
    job_id = f"turbo_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize scraper
    scraper = TwitterScraper()
    
    # Test with 50 tweets (triggers TURBO MODE)
    result_filename = scraper.scrape(
        keyword="technology",
        num_tweets=50,
        job_id=job_id
    )
    
    if result_filename:
        print("\n" + "=" * 40)
        print("✅ TURBO MODE TEST SUCCESSFUL!")
        print("=" * 40)
        print(f"📁 File: {result_filename}")
        
        # Count tweets
        import csv
        csv_path = f"scraped_data/{result_filename}"
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                tweets = list(reader)
                count = len(tweets)
            
            print(f"📊 Tweets collected: {count}/50")
            
            if count >= 45:  # Allow some variance
                print("🎉 SUCCESS: Good tweet collection!")
            else:
                print(f"⚠️  WARNING: Low count ({count}/50)")
                
            # Show sample
            if tweets:
                sample = tweets[0]
                print(f"\n📝 Sample tweet:")
                print(f"   @{sample.get('username', 'Unknown')}: {sample.get('text', 'No text')[:80]}...")
                
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
    else:
        print("\n❌ TURBO MODE TEST FAILED")

if __name__ == "__main__":
    quick_turbo_test()