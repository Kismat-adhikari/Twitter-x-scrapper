from scraper.playwright_scraper import TwitterScraper

def test_multiple_hashtags():
    """Test multiple hashtag handling"""
    scraper = TwitterScraper()
    
    print("🔗 MULTIPLE HASHTAG URL BUILDING TEST")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Few hashtags",
            "keyword": "AI",
            "hashtag": "AI, ML, tech",
            "expected": "Should work normally"
        },
        {
            "name": "Many hashtags",
            "keyword": "technology",
            "hashtag": "AI, ML, tech, programming, coding, python, javascript, data",
            "expected": "Should work normally (8 hashtags)"
        },
        {
            "name": "LOTS of hashtags",
            "keyword": "",
            "hashtag": "AI, ML, tech, programming, coding, python, javascript, data, science, analytics, bigdata, cloud, aws, azure",
            "expected": "Should work normally (14 hashtags)"
        },
        {
            "name": "Multiple keywords + many hashtags",
            "keyword": "AI, machine learning, deep learning, neural networks",
            "hashtag": "AI, ML, tech, programming, coding, python, tensorflow, pytorch",
            "expected": "Should simplify (too complex)"
        },
        {
            "name": "Extreme case",
            "keyword": "AI, ML, data science, machine learning, deep learning, computer vision",
            "hashtag": "AI, ML, tech, programming, coding, python, javascript, data, science, analytics, bigdata, cloud, aws, azure, tensorflow, pytorch",
            "expected": "Should simplify (very complex)"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test['name']}")
        print(f"   Keywords: '{test['keyword']}'")
        print(f"   Hashtags: '{test['hashtag']}'")
        print(f"   Expected: {test['expected']}")
        
        url = scraper.build_url(test['keyword'], test['hashtag'], '', '')
        print(f"   Result: {url}")
        
        # Count hashtags in final URL
        hashtag_count = url.count('%23')  # %23 is URL encoded #
        print(f"   Final hashtag count: {hashtag_count}")
        print()

if __name__ == "__main__":
    test_multiple_hashtags()