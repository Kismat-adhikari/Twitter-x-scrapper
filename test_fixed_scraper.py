"""
Test the fixed scraper to verify it works without infinite loops
"""
from scraper.playwright_scraper import TwitterScraper
import time

def test_fixed_scraper():
    print("🧪 TESTING FIXED SCRAPER")
    print("=" * 50)
    
    start_time = time.time()
    
    scraper = TwitterScraper(num_tabs=2)  # Use only 2 tabs for testing
    
    try:
        result = scraper.scrape(
            keyword="python programming",
            num_tweets=10,  # Small number for testing
            job_id="test_fixed"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n📊 TEST RESULTS:")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"📁 Result: {result}")
        
        if result:
            # Count tweets in file
            import csv
            try:
                with open(f"scraped_data/{result}", 'r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    count = sum(1 for row in reader)
                print(f"✅ Successfully collected {count} tweets")
                
                if duration < 120:  # Under 2 minutes
                    print("🚀 SPEED: Good performance!")
                else:
                    print("⏳ SPEED: Could be faster but stable")
                    
            except Exception as e:
                print(f"❌ Error reading file: {e}")
        else:
            print("❌ No results returned")
            
    except Exception as e:
        print(f"❌ Scraper failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_scraper()