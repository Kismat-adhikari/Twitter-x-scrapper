"""
Twitter API-based scraper that extracts real engagement metrics
Uses Playwright to intercept API calls and extract engagement data
"""
import json
import time
import random
from playwright.sync_api import sync_playwright
from urllib.parse import quote

class TwitterAPIScraper:
    def __init__(self):
        self.api_responses = []
        self.tweets_data = []
        
    def intercept_response(self, response):
        """Intercept Twitter API responses to extract tweet data"""
        try:
            # Look for Twitter's GraphQL API endpoints
            if 'api.twitter.com' in response.url or 'x.com/i/api' in response.url:
                if 'SearchTimeline' in response.url or 'TweetDetail' in response.url:
                    try:
                        data = response.json()
                        self.api_responses.append(data)
                        self.extract_tweets_from_api(data)
                    except:
                        pass
        except Exception as e:
            pass
    
    def extract_tweets_from_api(self, data):
        """Extract tweet data from API response"""
        try:
            # Navigate through Twitter's API response structure
            if isinstance(data, dict):
                # Look for tweet entries
                instructions = self._find_key(data, 'instructions')
                if instructions:
                    for instruction in instructions:
                        if isinstance(instruction, dict):
                            entries = instruction.get('entries', [])
                            for entry in entries:
                                self._process_entry(entry)
                
                # Also check for direct tweet data
                tweets = self._find_key(data, 'tweets')
                if tweets and isinstance(tweets, dict):
                    for tweet_id, tweet_data in tweets.items():
                        self._process_tweet_data(tweet_data)
        except Exception as e:
            print(f"Error extracting from API: {e}")
    
    def _find_key(self, obj, key):
        """Recursively find a key in nested dict/list"""
        if isinstance(obj, dict):
            if key in obj:
                return obj[key]
            for v in obj.values():
                result = self._find_key(v, key)
                if result is not None:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = self._find_key(item, key)
                if result is not None:
                    return result
        return None
    
    def _process_entry(self, entry):
        """Process a timeline entry"""
        try:
            if not isinstance(entry, dict):
                return
            
            # Get tweet result
            content = entry.get('content', {})
            item_content = content.get('itemContent', {})
            tweet_results = item_content.get('tweet_results', {})
            result = tweet_results.get('result', {})
            
            if result:
                self._process_tweet_data(result)
        except Exception as e:
            pass
    
    def _process_tweet_data(self, tweet_data):
        """Extract engagement metrics from tweet data"""
        try:
            if not isinstance(tweet_data, dict):
                return
            
            # Get legacy data (contains engagement metrics)
            legacy = tweet_data.get('legacy', {})
            if not legacy:
                return
            
            # Extract core data
            tweet_id = legacy.get('id_str', '')
            text = legacy.get('full_text', '')
            
            # Extract engagement metrics
            likes = legacy.get('favorite_count', 0)
            retweets = legacy.get('retweet_count', 0)
            replies = legacy.get('reply_count', 0)
            quotes = legacy.get('quote_count', 0)
            bookmarks = legacy.get('bookmark_count', 0)
            
            # Get user data
            user_data = tweet_data.get('core', {}).get('user_results', {}).get('result', {})
            if not user_data:
                user_data = legacy.get('user', {})
            
            user_legacy = user_data.get('legacy', {})
            username = user_legacy.get('screen_name', 'unknown')
            display_name = user_legacy.get('name', username)
            verified = user_data.get('is_blue_verified', False) or user_legacy.get('verified', False)
            
            # Get timestamp
            created_at = legacy.get('created_at', '')
            
            # Get language
            lang = legacy.get('lang', '')
            
            # Check if it's a retweet
            is_retweet = 'retweeted_status_result' in legacy or text.startswith('RT @')
            
            # Skip retweets if needed
            if is_retweet:
                return
            
            # Only include tweets with engagement > 0
            if likes == 0 and retweets == 0 and replies == 0:
                return
            
            # Extract hashtags and mentions
            entities = legacy.get('entities', {})
            hashtags = ', '.join([f"#{tag['text']}" for tag in entities.get('hashtags', [])])
            mentions = ', '.join([f"@{mention['screen_name']}" for mention in entities.get('user_mentions', [])])
            
            # Extract media URLs
            media = entities.get('media', [])
            media_urls = ', '.join([m.get('media_url_https', '') for m in media])
            
            # Build tweet object
            tweet = {
                'tweet_id': tweet_id,
                'tweet_url': f'https://x.com/{username}/status/{tweet_id}',
                'username': username,
                'display_name': display_name,
                'verified': 'Yes' if verified else 'No',
                'text': text.replace('\n', ' ').replace('"', '""'),
                'timestamp': created_at,
                'language': lang,
                'tweet_type': 'original',
                'likes': str(likes),
                'retweets': str(retweets),
                'replies': str(replies),
                'quotes': str(quotes),
                'bookmarks': str(bookmarks),
                'views': '',  # Views not always available
                'engagement_rate': '',
                'hashtags': hashtags,
                'mentions': mentions,
                'media_urls': media_urls,
                'is_original': 'true',
                'tweet_link': f'https://x.com/{username}/status/{tweet_id}',
                'profile_link': f'https://x.com/{username}'
            }
            
            # Check if we already have this tweet
            if not any(t['tweet_id'] == tweet_id for t in self.tweets_data):
                self.tweets_data.append(tweet)
                print(f"✅ Extracted tweet: {username} - {likes} likes, {retweets} RTs, {replies} replies")
        
        except Exception as e:
            print(f"Error processing tweet data: {e}")
    
    def scrape_with_api(self, search_url, num_tweets, cookies):
        """Scrape tweets using API interception"""
        print(f"🔍 Starting API-based scraping...")
        print(f"🎯 Target: {num_tweets} tweets")
        
        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                context = browser.new_context()
                
                # Add cookies for authentication
                if cookies:
                    context.add_cookies(cookies)
                    print(f"🔐 Added {len(cookies)} cookies for authentication")
                
                page = context.new_page()
                
                # Set up response interception
                page.on('response', self.intercept_response)
                
                # Navigate to search page
                print(f"🌐 Navigating to: {search_url}")
                page.goto(search_url, timeout=30000)
                time.sleep(3)  # Wait for initial load
                
                # Close any popups
                try:
                    close_btn = page.query_selector('[aria-label="Close"]')
                    if close_btn:
                        close_btn.click()
                        time.sleep(1)
                except:
                    pass
                
                # Scroll to load more tweets
                max_scrolls = 30
                no_new_tweets_count = 0
                
                for scroll in range(max_scrolls):
                    if len(self.tweets_data) >= num_tweets:
                        print(f"✅ Reached target: {len(self.tweets_data)} tweets")
                        break
                    
                    previous_count = len(self.tweets_data)
                    
                    # Scroll down
                    page.evaluate('window.scrollBy(0, window.innerHeight * 3)')
                    time.sleep(random.uniform(1.5, 2.5))
                    
                    # Check if we got new tweets
                    if len(self.tweets_data) == previous_count:
                        no_new_tweets_count += 1
                        print(f"⏳ No new tweets... ({no_new_tweets_count}/5)")
                    else:
                        no_new_tweets_count = 0
                        print(f"📊 Progress: {len(self.tweets_data)}/{num_tweets} tweets")
                    
                    # Stop if no new tweets for 5 scrolls
                    if no_new_tweets_count >= 5:
                        print(f"⚠️ No new tweets found, stopping")
                        break
                
                browser.close()
                
                print(f"✅ Scraping complete! Collected {len(self.tweets_data)} tweets with real engagement")
                return self.tweets_data[:num_tweets]
        
        except Exception as e:
            print(f"❌ Error during API scraping: {e}")
            import traceback
            traceback.print_exc()
            return []
