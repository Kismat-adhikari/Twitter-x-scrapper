from scraper.playwright_scraper import TwitterScraper
import time

def test_simple_vs_complex():
    """Test simple vs complex search terms"""
    scraper = TwitterScraper()
    
    print("🧪 TESTING SIMPLE VS COMPLEX SEARCH TERMS")
    print("=" * 50)
    
    tests = [
        {"name": "Simple AI", "keyword": "AI", "hashtag": "", "target": 10},
        {"name": "Simple tech", "keyword": "technology", "hashtag": "", "target": 10},
        {"name": "Medium complexity", "keyword": "AI machine learning", "hashtag": "AI", "target": 10},
        {"name": "Too complex", "keyword": "AI, ML, CS, deep learning", "hashtag": "AI, ML, CS", "target": 10}
    ]
    
    for test in tests:
        print(f"\n🔍 Test: {test['name']}")
        print(f"   Keyword: '{test['keyword']}'")
        print(f"   Hashtag: '{test['hashtag']}'")
        
        try:
            start_time = time.time()
            job_id = scraper.scrape(
                keyword=test['keyword'],
                hashtag=test['hashtag'],
                num_tweets=test['target']
            )
            duration = time.time() - start_time
            
            # Quick check of results
            csv_path = f"scraped_data/{job_id}"
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                actual_tweets = len(lines) - 1  # Minus header
                
            print(f"   ✅ Result: {actual_tweets} tweets in {duration:.1f}s")
            
            # Check for UI elements in first few lines
            ui_elements = 0
            for line in lines[1:6]:  # Check first 5 tweets
                if ('fallback_' in line and 
                    ('Top Latest People' in line or 'No results' in line or 'See new posts' in line)):
                    ui_elements += 1
            
            if ui_elements > 2:
                print(f"   ⚠️  Warning: {ui_elements}/5 entries are UI elements")
            else:
                print(f"   ✅ Quality: Good content detected")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        time.sleep(2)  # Brief pause between tests

if __name__ == "__main__":
    test_simple_vs_complex()