#!/usr/bin/env python3
"""
Test multiple keywords functionality
"""

from scraper.playwright_scraper import TwitterScraper
from datetime import datetime

def test_multiple_keywords():
    """Test multiple keywords search"""
    print("🧪 Testing Multiple Keywords Support")
    print("=" * 40)
    
    # Test different keyword combinations
    test_cases = [
        "AI machine learning",
        "\"artificial intelligence\" technology",
        "crypto bitcoin ethereum",
        "python programming code"
    ]
    
    for i, keywords in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: '{keywords}'")
        
        # Create timestamp for job ID
        job_id = f"multi_test_{i}_{datetime.now().strftime('%H%M%S')}"
        
        # Initialize scraper
        scraper = TwitterScraper()
        
        # Test with 10 tweets to keep it quick
        result_filename = scraper.scrape(
            keyword=keywords,
            num_tweets=10,
            job_id=job_id
        )
        
        if result_filename:
            print(f"   ✅ Success: {result_filename}")
            
            # Quick count check
            import csv
            csv_path = f"scraped_data/{result_filename}"
            try:
                with open(csv_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    tweets = list(reader)
                    count = len(tweets)
                print(f"   📊 Collected: {count} tweets")
                
                if tweets:
                    # Show sample text to verify relevance
                    sample_text = tweets[0].get('text', 'No text')[:60]
                    print(f"   📝 Sample: {sample_text}...")
                    
            except Exception as e:
                print(f"   ⚠️  Error reading: {e}")
        else:
            print(f"   ❌ Failed")
        
        if i < len(test_cases):
            print("   Waiting 5 seconds before next test...")
            import time
            time.sleep(5)

if __name__ == "__main__":
    test_multiple_keywords()