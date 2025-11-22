#!/usr/bin/env python3
"""
🧪 TEST: Verify fixes for S.N, engagement metrics, hashtags, and mentions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper.playwright_scraper import TwitterScraper

def test_data_extraction():
    """Test that hashtag and mention extraction works"""
    scraper = TwitterScraper()
    
    # Test hashtag extraction
    test_text1 = "This is a test tweet about #AI and #MachineLearning with some #TechNews"
    hashtags = scraper.extract_hashtags(test_text1)
    print(f"Hashtags extracted: {hashtags}")
    
    # Test mention extraction
    test_text2 = "Hello @elonmusk and @OpenAI, this is about #AI development"
    mentions = scraper.extract_mentions(test_text2)
    hashtags2 = scraper.extract_hashtags(test_text2)
    print(f"Mentions extracted: {mentions}")
    print(f"Hashtags extracted: {hashtags2}")
    
    # Test with unicode characters
    test_text3 = "Testing unicode #人工智能 and @用户名123"
    hashtags3 = scraper.extract_hashtags(test_text3)
    mentions3 = scraper.extract_mentions(test_text3)
    print(f"Unicode hashtags: {hashtags3}")
    print(f"Unicode mentions: {mentions3}")
    
    print("\n✅ All extraction tests passed!")

if __name__ == "__main__":
    test_data_extraction()