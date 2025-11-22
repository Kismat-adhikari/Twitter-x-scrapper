from scraper.playwright_scraper import TwitterScraper

# Test URL building
scraper = TwitterScraper()

# Test cases
test_cases = [
    {"keyword": "AI technology", "hashtag": "", "username": ""},
    {"keyword": "", "hashtag": "AI", "username": ""},
    {"keyword": "", "hashtag": "AI, machine learning, tech", "username": ""},
    {"keyword": "machine learning", "hashtag": "AI, tech", "username": ""},
]

print("🔗 URL Building Test:")
print("=" * 50)

for i, case in enumerate(test_cases, 1):
    url = scraper.build_url(case["keyword"], case["hashtag"], case["username"], "")
    print(f"Test {i}:")
    print(f"  Input - keyword: '{case['keyword']}', hashtag: '{case['hashtag']}', username: '{case['username']}'")
    print(f"  Output: {url}")
    print()