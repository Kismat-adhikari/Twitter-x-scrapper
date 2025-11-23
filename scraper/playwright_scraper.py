"""
Fixed and simplified Twitter scraper with robust error handling
"""
import os
import csv
import time
import random
import re
import json
import threading
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
from scraper.proxy_manager import ProxyManager
from scraper.csv_handler import CSVHandler
from scraper.fast_csv_handler import FastCSVHandler
from scraper.cookie_loader import load_cookies

class TwitterScraper:
    def __init__(self, num_tabs=None):  # Dynamic tab count
        self.num_tabs = num_tabs
        self.proxy_manager = ProxyManager()
        self.cookies = load_cookies()
        self.csv_handler = None
        self.lock = threading.Lock()
        self.total_scraped = 0
        self.target_reached = False
        self.api_tweets = []  # Store tweets from API interception
        self.use_api_extraction = True  # Enable API-based extraction
        self.api_users = {}  # Cache users from API responses
        
        # User agent pool for better stealth
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        ]

    def scrape(self, keyword='', hashtag='', username='', tweet_url='', tweet_urls=None, num_tweets=100, job_id='', search_mode='top'):
        """Main scraping method with robust error handling
        
        Args:
            search_mode: 'top' (popular tweets), 'live' (latest tweets), or 'people' (from verified accounts)
        """
        # Handle bulk URLs first
        if tweet_urls and len(tweet_urls) > 0:
            return self._scrape_bulk_urls(tweet_urls, job_id)
        
        # Build search URL
        search_url = self.build_url(keyword, hashtag, username, tweet_url, search_mode)
        
        # Initialize CSV handler
        self.csv_handler = FastCSVHandler(job_id) if num_tweets >= 50 else CSVHandler(job_id)
        self.job_id = job_id
        self.target_tweets = num_tweets  # Store target for exact count checking
        
        # Optimized tab count for maximum speed
        if self.num_tabs is None:
            if num_tweets >= 200:
                self.num_tabs = 8  # Maximum for very large targets
            elif num_tweets >= 100:
                self.num_tabs = 6  # High for large targets
            elif num_tweets >= 50:
                self.num_tabs = 5  # Medium-high for medium targets
            else:
                self.num_tabs = 4  # Faster for small targets
        
        print(f"STARTING SCRAPE: {self.num_tabs} parallel tabs")
        print(f"Target: {num_tweets} tweets")
        print(f"URL: {search_url}")
        
        # Reset counters
        self.total_scraped = 0
        self.target_reached = False
        
        # Run parallel scraping
        with ThreadPoolExecutor(max_workers=self.num_tabs) as executor:
            futures = []
            for i in range(self.num_tabs):
                future = executor.submit(self.scrape_tab_simple, search_url, num_tweets, i)
                futures.append(future)
            
            # Wait for completion
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Tab error: {e}")
        
        final_count = self.csv_handler.get_tweet_count()
        print(f"Scraping complete! Collected {final_count} tweets")
        
        if hasattr(self.csv_handler, 'force_flush'):
            self.csv_handler.force_flush()
        
        return self.csv_handler.get_filename() if final_count > 0 else None

    def _intercept_api_response(self, response, tab_id):
        """Intercept Twitter API responses to extract real engagement data"""
        try:
            url = response.url
            # Look for Twitter's GraphQL API endpoints
            if ('api.twitter.com' in url or 'x.com/i/api' in url) and \
               ('SearchTimeline' in url or 'TweetDetail' in url or 'UserTweets' in url):
                try:
                    data = response.json()
                    self._extract_tweets_from_api(data, tab_id)
                except:
                    pass
        except Exception as e:
            pass
    
    def _extract_tweets_from_api(self, data, tab_id):
        """Extract tweet data with real engagement from API response"""
        try:
            if not isinstance(data, dict):
                return
            
            # Store users data for lookup
            self.api_users = self._find_in_dict(data, 'users') or {}
            
            # Navigate through Twitter's API response structure
            instructions = self._find_in_dict(data, 'instructions')
            if instructions and isinstance(instructions, list):
                for instruction in instructions:
                    if isinstance(instruction, dict):
                        entries = instruction.get('entries', [])
                        for entry in entries:
                            # Stop processing if we've reached target
                            if self.target_reached or self.csv_handler.get_tweet_count() >= self.target_tweets:
                                return
                            self._process_api_entry(entry, tab_id)
            
            # Also check for direct tweet data
            tweets = self._find_in_dict(data, 'tweets')
            if tweets and isinstance(tweets, dict):
                for tweet_id, tweet_data in tweets.items():
                    # Stop processing if we've reached target
                    if self.target_reached or self.csv_handler.get_tweet_count() >= self.target_tweets:
                        return
                    self._process_api_tweet(tweet_data, tab_id, None)
        except Exception as e:
            pass
    
    def _find_in_dict(self, obj, key):
        """Recursively find a key in nested dict/list"""
        if isinstance(obj, dict):
            if key in obj:
                return obj[key]
            for v in obj.values():
                result = self._find_in_dict(v, key)
                if result is not None:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = self._find_in_dict(item, key)
                if result is not None:
                    return result
        return None
    
    def _process_api_entry(self, entry, tab_id):
        """Process a timeline entry from API"""
        try:
            if not isinstance(entry, dict):
                return
            
            content = entry.get('content', {})
            item_content = content.get('itemContent', {})
            tweet_results = item_content.get('tweet_results', {})
            result = tweet_results.get('result', {})
            
            if result:
                # Pass the full entry for better user data extraction
                self._process_api_tweet(result, tab_id, entry)
        except:
            pass
    
    def _process_api_tweet(self, tweet_data, tab_id, entry=None):
        """Extract engagement metrics from API tweet data"""
        try:
            if not isinstance(tweet_data, dict):
                return
            
            # Get legacy data (contains engagement metrics)
            legacy = tweet_data.get('legacy', {})
            if not legacy:
                return
            
            # Extract core data
            tweet_id = legacy.get('id_str', '')
            if not tweet_id:
                return
            
            text = legacy.get('full_text', '')
            
            # Extract engagement metrics - THE KEY FIX!
            likes = legacy.get('favorite_count', 0)
            retweets = legacy.get('retweet_count', 0)
            replies = legacy.get('reply_count', 0)
            quotes = legacy.get('quote_count', 0)
            bookmarks = legacy.get('bookmark_count', 0)
            
            # Extract views (sometimes in tweet_data.views, sometimes in legacy)
            views = 0
            if 'views' in tweet_data:
                views_data = tweet_data.get('views', {})
                if isinstance(views_data, dict):
                    view_count = views_data.get('count', 0)
                    # Convert to int if it's a string
                    if isinstance(view_count, str):
                        try:
                            views = int(view_count)
                        except:
                            views = 0
                    else:
                        views = view_count
                elif isinstance(views_data, (int, str)):
                    try:
                        views = int(views_data)
                    except:
                        views = 0
            
            # Calculate engagement rate (total engagement / views * 100)
            # If no views, calculate based on followers (but we don't have that, so use total engagement)
            total_engagement = likes + retweets + replies + quotes + bookmarks
            if views > 0:
                engagement_rate = round((total_engagement / views) * 100, 2)
            else:
                engagement_rate = 0
            
            # FILTER: Only include tweets with engagement > 0
            if likes == 0 and retweets == 0 and replies == 0:
                return
            
            # Get user data - try ALL possible paths in the API response
            username = None
            display_name = None
            verified = False
            profile_bio = ''
            profile_location = ''
            profile_website = ''
            profile_email = ''
            followers_count = 0
            following_count = 0
            
            # Method 1: Try core.user_results.result.core (CORRECT location for screen_name!)
            try:
                core = tweet_data.get('core', {})
                if core:
                    user_results = core.get('user_results', {})
                    if user_results:
                        user_result = user_results.get('result', {})
                        if user_result and isinstance(user_result, dict):
                            # The screen_name and name are in user_result.core, NOT user_result.legacy!
                            user_core = user_result.get('core', {})
                            if user_core:
                                username = user_core.get('screen_name')
                                display_name = user_core.get('name')
                            
                            # Verification status is at top level or in legacy
                            user_legacy = user_result.get('legacy', {})
                            verified = user_result.get('is_blue_verified', False)
                            if not verified and user_legacy:
                                verified = user_legacy.get('verified', False)
                            
                            # Extract profile information from user_legacy
                            profile_bio = ''
                            profile_location = ''
                            profile_website = ''
                            profile_email = ''
                            followers_count = 0
                            following_count = 0
                            
                            if user_legacy:
                                # Bio/Description
                                profile_bio = user_legacy.get('description', '')
                                
                                # Location
                                profile_location = user_legacy.get('location', '')
                                
                                # Followers and Following
                                followers_count = user_legacy.get('followers_count', 0)
                                following_count = user_legacy.get('friends_count', 0)
                                
                                # Website/URL - check entities for expanded URL
                                url_entities = user_legacy.get('entities', {}).get('url', {}).get('urls', [])
                                if url_entities and len(url_entities) > 0:
                                    # Get the expanded URL (actual website)
                                    profile_website = url_entities[0].get('expanded_url', '')
                                    if not profile_website:
                                        profile_website = url_entities[0].get('url', '')
                                
                                # Try to extract email from bio (if present)
                                if profile_bio:
                                    import re
                                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                                    email_matches = re.findall(email_pattern, profile_bio)
                                    if email_matches:
                                        profile_email = email_matches[0]
                                
                                # Also check description entities for URLs
                                desc_entities = user_legacy.get('entities', {}).get('description', {}).get('urls', [])
                                if desc_entities and not profile_website:
                                    for url_entity in desc_entities:
                                        expanded = url_entity.get('expanded_url', '')
                                        if expanded:
                                            profile_website = expanded
                                            break
            except Exception as e:
                pass
            
            # Method 2: Try direct user field in tweet_data
            if not username:
                try:
                    user_obj = tweet_data.get('user', {})
                    if user_obj:
                        username = user_obj.get('screen_name') or user_obj.get('legacy', {}).get('screen_name')
                        display_name = user_obj.get('name') or user_obj.get('legacy', {}).get('name')
                        verified = user_obj.get('verified', False)
                except:
                    pass
            
            # Method 3: Try legacy.user_id_str and look up in cached users
            if not username:
                try:
                    user_id = legacy.get('user_id_str')
                    if user_id:
                        # Try cached users first
                        if hasattr(self, 'api_users') and user_id in self.api_users:
                            user_info = self.api_users[user_id]
                            username = user_info.get('screen_name')
                            display_name = user_info.get('name')
                            verified = user_info.get('verified', False)
                        # Try to find user in entry data
                        elif entry:
                            users = self._find_in_dict(entry, 'users')
                            if users and isinstance(users, dict) and user_id in users:
                                user_info = users[user_id]
                                username = user_info.get('screen_name')
                                display_name = user_info.get('name')
                                verified = user_info.get('verified', False)
                except:
                    pass
            
            # Method 4: Extract username from conversation_id_str pattern
            if not username:
                try:
                    # Sometimes we can infer from the tweet structure
                    conversation_id = legacy.get('conversation_id_str')
                    if conversation_id == tweet_id:
                        # This is the original tweet, try to get user from other fields
                        pass
                except:
                    pass
            
            # Fallback: Use 'unknown' if still not found
            if not username:
                username = 'unknown'
            if not display_name:
                display_name = username
            
            # Get timestamp
            created_at = legacy.get('created_at', '')
            
            # Get language
            lang = legacy.get('lang', '')
            
            # Check if it's a retweet
            is_retweet = 'retweeted_status_result' in legacy or text.startswith('RT @')
            if is_retweet:
                return
            
            # Extract hashtags and mentions
            entities = legacy.get('entities', {})
            hashtags = ', '.join([f"#{tag['text']}" for tag in entities.get('hashtags', [])])
            mentions = ', '.join([f"@{mention['screen_name']}" for mention in entities.get('user_mentions', [])])
            
            # Extract media URLs
            media = entities.get('media', [])
            media_urls = ', '.join([m.get('media_url_https', '') for m in media])
            
            # Clean text for CSV
            text = text.replace('\n', ' ').replace('"', '""')
            
            # Build tweet object with REAL engagement metrics
            tweet = {
                'tweet_id': tweet_id,
                'tweet_url': f'https://x.com/{username}/status/{tweet_id}',
                'username': username,
                'display_name': display_name,
                'verified': 'Yes' if verified else 'No',
                'text': text,
                'timestamp': created_at,
                'language': lang,
                'tweet_type': 'original',
                'likes': str(likes),  # REAL engagement!
                'retweets': str(retweets),  # REAL engagement!
                'replies': str(replies),  # REAL engagement!
                'quotes': str(quotes),  # REAL engagement!
                'bookmarks': str(bookmarks),  # REAL engagement!
                'views': str(views) if views > 0 else '',  # REAL views!
                'engagement_rate': f'{engagement_rate}%' if engagement_rate > 0 else '',
                'hashtags': hashtags,
                'mentions': mentions,
                'media_urls': media_urls,
                'is_original': 'true',
                'tweet_link': f'https://x.com/{username}/status/{tweet_id}',
                'profile_link': f'https://x.com/{username}',
                'profile_bio': profile_bio.replace('\n', ' ').replace('"', '""') if profile_bio else '',
                'profile_location': profile_location,
                'profile_website': profile_website,
                'profile_email': profile_email,
                'followers_count': str(followers_count),
                'following_count': str(following_count)
            }
            
            # Add to CSV if unique and has engagement
            # Check if we've already reached the target before adding
            current_count = self.csv_handler.get_tweet_count()
            if current_count >= self.target_tweets:
                return  # Stop processing more tweets
            
            if self.csv_handler and self.csv_handler.add_tweet(tweet):
                with self.lock:
                    self.total_scraped += 1
                current_count = self.csv_handler.get_tweet_count()
                print(f"Tab {tab_id}: API tweet - {username}: {likes} likes, {retweets} RTs, {replies} replies (Total: {current_count})")
                
                # Check again after adding
                if current_count >= self.target_tweets:
                    self.target_reached = True
        
        except Exception as e:
            pass

    def scrape_tab_simple(self, search_url, num_tweets, tab_id):
        """Simplified, more reliable tab scraping"""
        print(f"Tab {tab_id}: Starting...")
        
        try:
            with sync_playwright() as p:
                # Get a random proxy for this tab for better distribution
                # Proxies enabled for better rate limiting and avoiding blocks
                use_proxies = True  # Enabled to avoid getting blocked
                
                proxy = None
                if use_proxies:
                    # Use random proxy selection for better distribution
                    proxy = self.proxy_manager.get_random_proxy()
                    if proxy:
                        print(f"Tab {tab_id}: Using proxy {proxy.get('server', 'unknown')}")
                    else:
                        print(f"Tab {tab_id}: No proxy available, using direct connection")
                
                # Launch browser with global proxy setting (required by Playwright)
                # If proxy is None, Playwright will use direct connection
                browser_args = [
                    '--no-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
                
                browser = p.chromium.launch(
                    headless=True,
                    args=browser_args,
                    proxy=proxy if proxy else None
                )
                
                # Create context with better stealth settings
                user_agent = random.choice(self.user_agents)
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={'width': 1366, 'height': 768},
                    locale='en-US',
                    timezone_id='America/New_York'
                )
                
                print(f"Tab {tab_id}: Using user agent: {user_agent[:50]}...")
                
                if not proxy:
                    print(f"Tab {tab_id}: Using direct connection (no proxies available)")
                
                if self.cookies:
                    context.add_cookies(self.cookies)
                
                page = context.new_page()
                
                # Add stealth JavaScript
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                
                # Set up API response interception for real engagement metrics
                if self.use_api_extraction:
                    page.on('response', lambda response: self._intercept_api_response(response, tab_id))
                
                # Navigate to URL with retries
                print(f"Tab {tab_id}: Navigating to search page...")
                max_retries = 3
                response = None
                
                for retry in range(max_retries):
                    try:
                        response = page.goto(search_url, timeout=45000, wait_until='domcontentloaded')
                        print(f"Tab {tab_id}: Response status: {response.status if response else 'None'}")
                        
                        if response and response.status == 200:
                            break
                        elif response and response.status in [429, 503]:
                            print(f"Tab {tab_id}: Rate limited (status {response.status}), marking proxy as failed")
                            if proxy:
                                self.proxy_manager.mark_failed(proxy)
                            time.sleep(random.uniform(5, 10))
                            return
                    except Exception as e:
                        print(f"Tab {tab_id}: Navigation attempt {retry + 1} failed: {e}")
                        if retry < max_retries - 1:
                            time.sleep(random.uniform(2, 4))
                        else:
                            return
                
                time.sleep(random.uniform(3, 5))  # Give more time to load
                
                # Debug: Check what we loaded
                title = page.title()
                current_url = page.url
                print(f"Tab {tab_id}: Page title: '{title}'")
                print(f"Tab {tab_id}: Current URL: {current_url}")
                
                # Enhanced blocking detection
                is_blocked = False
                blocking_reason = ""
                
                # Check for various blocking indicators
                if (title == "X" or 
                    "login" in title.lower() or 
                    "sign" in title.lower() or
                    "suspended" in title.lower() or
                    "unavailable" in title.lower()):
                    is_blocked = True
                    blocking_reason = f"Title indicates blocking: {title}"
                
                # Check page content for additional blocking indicators
                try:
                    page_content = page.content().lower()
                    blocking_indicators = [
                        "something went wrong",
                        "this account is suspended", 
                        "this account doesn't exist",
                        "rate limit exceeded",
                        "temporarily restricted",
                        "suspicious activity",
                        "page doesn't exist",
                        "try searching for something else",
                        "hmm...this page doesn't exist",
                        "this page doesn't exist"
                    ]
                    
                    for indicator in blocking_indicators:
                        if indicator in page_content:
                            is_blocked = True
                            blocking_reason = f"Content indicates blocking: {indicator}"
                            break
                            
                except Exception as e:
                    pass
                
                if is_blocked:
                    print(f"Tab {tab_id}: {blocking_reason}")
                    print(f"Tab {tab_id}: Marking proxy as failed and trying different search")
                    if proxy:
                        self.proxy_manager.mark_failed(proxy)
                    
                    # Try a simpler search approach
                    try:
                        # Try searching for just "AI" instead of complex query
                        simple_url = "https://x.com/search?q=AI&src=typed_query&f=top"
                        print(f"Tab {tab_id}: Trying simpler search: {simple_url}")
                        page.goto(simple_url, timeout=30000)
                        time.sleep(random.uniform(2, 4))
                        
                        new_title = page.title()
                        print(f"Tab {tab_id}: Simple search title: {new_title}")
                        
                        # If simple search also fails, skip this tab
                        if ("doesn't exist" in new_title.lower() or 
                            new_title == "X" or 
                            "login" in new_title.lower()):
                            print(f"Tab {tab_id}: Simple search also failed, skipping tab")
                            return
                            
                    except Exception as e:
                        print(f"Tab {tab_id}: Simple search attempt failed: {e}")
                        return
                
                # Try to close any popups (faster)
                try:
                    close_btn = page.query_selector('[aria-label=\"Close\"]')
                    if close_btn:
                        close_btn.click()
                        time.sleep(0.3)
                except:
                    pass
                
                tweets_found = 0
                # Much more aggressive scrolling for larger targets
                if num_tweets >= 200:
                    max_scrolls = 300  # Very aggressive for 200+
                elif num_tweets >= 100:
                    max_scrolls = 200  # More aggressive for 100+
                elif num_tweets >= 50:
                    max_scrolls = 100  # Moderate for 50+
                else:
                    max_scrolls = 50   # Conservative for small targets
                    
                no_content_count = 0
                consecutive_no_tweets = 0  # Track consecutive failed extractions
                
                for scroll in range(max_scrolls):
                    if self.target_reached:
                        print(f"Tab {tab_id}: Target reached globally, stopping")
                        break
                    
                    # Extract tweets from current view
                    tweets = self.extract_tweets_simple(page)
                    
                    # Check if we're on a "no results" page or empty page
                    try:
                        page_content = page.content().lower()
                        no_results_indicators = [
                            'no results',
                            'try searching for something else',
                            'nothing here',
                            'no tweets found',
                            "hmm...this page doesn't exist",
                            "this page doesn't exist"
                        ]
                        
                        if any(indicator in page_content for indicator in no_results_indicators):
                            print(f"Tab {tab_id}: No results page detected, stopping")
                            break
                            
                        # Check if page is completely empty
                        if len(page_content) < 1000:  # Very small page likely means error
                            print(f"Tab {tab_id}: Page seems empty ({len(page_content)} chars), stopping")
                            break
                            
                    except Exception as e:
                        # If page content check fails, continue trying
                        print(f"Tab {tab_id}: Could not check page content: {e}")
                    
                    if tweets:
                        new_tweets = 0
                        for tweet in tweets:
                            # Check global count
                            current_count = self.csv_handler.get_tweet_count()
                            if current_count >= num_tweets:
                                self.target_reached = True
                                break
                            
                            # Add tweet if unique
                            if self.csv_handler.add_tweet(tweet):
                                new_tweets += 1
                                tweets_found += 1
                                with self.lock:
                                    self.total_scraped += 1
                        
                        if new_tweets > 0:
                            current_count = self.csv_handler.get_tweet_count()
                            print(f"Tab {tab_id}: +{new_tweets} tweets (Total: {current_count}/{num_tweets})")
                            no_content_count = 0
                        else:
                            no_content_count += 1
                    else:
                        no_content_count += 1
                        print(f"Tab {tab_id}: No tweets found in view {scroll + 1}")
                    
                    # Much more aggressive persistence for larger targets
                    current_total = self.csv_handler.get_tweet_count()
                    progress_ratio = current_total / num_tweets
                    
                    if num_tweets >= 200:
                        # For very large targets (200+), extremely persistent
                        if progress_ratio < 0.2:
                            max_no_content = 25   # Very persistent early on
                        elif progress_ratio < 0.5:
                            max_no_content = 20   # Persistent early-mid
                        elif progress_ratio < 0.8:
                            max_no_content = 15   # Still persistent mid-way
                        else:
                            max_no_content = 12   # Persistent near end
                    elif num_tweets >= 100:
                        # For large targets (100-199), very persistent
                        if progress_ratio < 0.3:
                            max_no_content = 20   # Very persistent early on
                        elif progress_ratio < 0.6:
                            max_no_content = 15   # Persistent mid-way
                        elif progress_ratio < 0.85:
                            max_no_content = 12   # Still persistent
                        else:
                            max_no_content = 10   # Try harder near end
                    elif num_tweets >= 50:
                        # For medium targets (50-99), moderately persistent
                        if progress_ratio < 0.5:
                            max_no_content = 15   # Persistent early
                        elif progress_ratio < 0.8:
                            max_no_content = 12   # Moderate persistence
                        else:
                            max_no_content = 10   # Still trying near end
                    else:
                        max_no_content = 8  # Conservative for small targets
                    
                    if no_content_count >= max_no_content:
                        print(f"Tab {tab_id}: No new content for {max_no_content} attempts (progress: {progress_ratio:.1%}), stopping")
                        break
                    
                    # More aggressive scrolling with variable speeds
                    if num_tweets >= 200:
                        # Largest targets: very aggressive scrolling
                        scroll_distance = random.uniform(8, 12) * page.evaluate('window.innerHeight')
                        page.evaluate(f'window.scrollBy(0, {scroll_distance})')
                    elif num_tweets >= 100:
                        # Large targets: aggressive scrolling
                        scroll_distance = random.uniform(6, 10) * page.evaluate('window.innerHeight')
                        page.evaluate(f'window.scrollBy(0, {scroll_distance})')
                    else:
                        # Smaller targets: moderate scrolling
                        scroll_distance = random.uniform(4, 8) * page.evaluate('window.innerHeight')
                        page.evaluate(f'window.scrollBy(0, {scroll_distance})')
                    
                    # Adaptive wait times based on performance and target
                    if no_content_count >= 8:
                        sleep_time = random.uniform(1.5, 2.0)  # Longer wait when really struggling
                    elif no_content_count >= 5:
                        sleep_time = random.uniform(1.0, 1.5)  # Moderate wait when struggling
                    elif no_content_count >= 3:
                        sleep_time = random.uniform(0.8, 1.2)  # Short wait when struggling
                    elif num_tweets >= 200:
                        sleep_time = random.uniform(0.4, 0.6)  # Fast for very large targets
                    elif num_tweets >= 100:
                        sleep_time = random.uniform(0.5, 0.8)  # Moderate for large targets
                    else:
                        sleep_time = random.uniform(0.3, 0.6)  # Quick for smaller targets
                    
                    time.sleep(sleep_time)
                
                print(f"Tab {tab_id}: Finished with {tweets_found} tweets")
                browser.close()
                
        except Exception as e:
            print(f"Tab {tab_id}: Error: {e}")

    def extract_tweets_simple(self, page):
        """Simplified tweet extraction with basic selectors"""
        tweets = []
        
        try:
            # Minimal content loading wait (optimized for speed)
            time.sleep(0.1)
            
            # Look for tweet articles with multiple strategies
            articles = page.query_selector_all('article')
            
            # If no articles, try alternative selectors
            if not articles:
                # Try alternative selectors for tweet containers
                alt_selectors = [
                    '[data-testid="tweet"]',
                    '[data-testid="cellInnerDiv"]',
                    'div[data-testid*="tweet"]',
                    '[role="article"]',
                    '.css-175oi2r[data-testid]',  # Generic Twitter container
                    '[data-testid="primaryColumn"] > div > div',  # Timeline items
                    'div[aria-label*="timeline"]',  # Timeline specific
                    'section[aria-labelledby] article',  # Section articles
                    '.r-1d09ksm',  # CSS class often used for tweets
                    '.r-18u37iz'   # Another common CSS class
                ]
                
                for selector in alt_selectors:
                    articles = page.query_selector_all(selector)
                    if articles:
                        print(f"Found {len(articles)} articles using selector: {selector}")
                        break
            else:
                print(f"Found {len(articles)} articles using standard selector")
            
            if not articles:
                # No articles found - this likely means the page has no tweets or is blocked
                print("No articles found - likely empty page, no tweets, or authentication required")
                return tweets
            
            for i, article in enumerate(articles[:50]):  # Aggressive: 50 per extraction for speed
                try:
                    # Look for tweet text in various ways
                    text_elem = None
                    text_selectors = [
                        '[data-testid="tweetText"]',
                        'div[lang]',
                        'span[dir="auto"]',
                        'div[data-testid*="text"]',
                        '.css-1rynq56',
                        '.css-901oao',
                        'span',
                        'div'
                    ]
                    
                    for selector in text_selectors:
                        text_elems = article.query_selector_all(selector)
                        if text_elems:
                            # Try to find the best text element (longest text)
                            best_elem = max(text_elems, key=lambda e: len(e.inner_text().strip()) if e.inner_text() else 0)
                            if best_elem and len(best_elem.inner_text().strip()) > 10:
                                text_elem = best_elem
                                break
                    
                    if not text_elem:
                        continue
                    
                    text = text_elem.inner_text().strip()
                    if not text or len(text) < 10:  # Minimum length for real tweets
                        continue
                    
                    # Skip obvious UI elements by content
                    ui_elements = [
                        'notifications', 'home', 'explore', 'messages', 'bookmarks',
                        'top latest people media lists', 'people you follow', 'advanced search',
                        'politics · trending', 'trending', 'what\'s happening',
                        'kismat adhikari', 'see new tweets', 'show this thread',
                        'top latest people media', 'latest people media lists',
                        'people media lists', 'top latest', 'media lists',
                        'click to follow', 'follow'
                    ]
                    
                    if any(ui_elem in text.lower() for ui_elem in ui_elements):
                        continue
                    
                    # Skip very short text that's likely UI
                    if len(text.split()) < 4:  # Require at least 4 words for a real tweet
                        continue
                    
                    # Skip if it's only navigation terms
                    nav_only_terms = ['top', 'latest', 'people', 'media', 'lists', 'home', 'explore', 'trending']
                    text_words = [word.lower().strip('.,!?') for word in text.split()]
                    if all(word in nav_only_terms for word in text_words):
                        continue
                    
                    # Clean text for CSV: remove newlines and normalize whitespace
                    text = ' '.join(text.split())  # This removes all extra whitespace and newlines
                    text = text.replace('"', '""')  # Escape quotes for CSV
                    
                    # Skip promoted content and retweets
                    if 'Promoted' in text or text.startswith('RT @'):
                        continue
                    
                    # Try to get username and tweet ID from links - enhanced approach
                    username = 'unknown'
                    tweet_id = f'tweet_{int(time.time())}_{i}'
                    
                    # First, try to get the article's main link
                    try:
                        # Method 1: Look for time/date links (most reliable)
                        time_selectors = [
                            'a[href*="/status/"]',
                            'time parent a',
                            'a time',
                            '[data-testid="Time"] a'
                        ]
                        
                        for selector in time_selectors:
                            time_links = article.query_selector_all(selector)
                            for link in time_links:
                                href = link.get_attribute('href')
                                if href and '/status/' in href:
                                    # Clean and parse href
                                    href = href.strip('/')
                                    if href.startswith('/'):
                                        href = href[1:]  # Remove leading slash
                                    
                                    # Extract from pattern: username/status/id
                                    parts = href.split('/')
                                    status_index = -1
                                    for idx, part in enumerate(parts):
                                        if part == 'status':
                                            status_index = idx
                                            break
                                    
                                    if status_index > 0 and status_index + 1 < len(parts):
                                        username = parts[status_index - 1]
                                        tweet_id = parts[status_index + 1].split('?')[0].split('#')[0]
                                        if username and tweet_id and tweet_id.isdigit():
                                            break
                            
                            if username != 'unknown' and tweet_id.isdigit():
                                break
                        
                        # Method 2: If still unknown, try profile links in article
                        if username == 'unknown':
                            profile_selectors = [
                                'a[href^="/"][href*="/"]:not([href*="/status/"]):not([href*="/search/"]):not([href*="/hashtag/"])',
                                '[data-testid="User-Name"] a',
                                '[data-testid="User-Names"] a'
                            ]
                            
                            for selector in profile_selectors:
                                profile_links = article.query_selector_all(selector)
                                for link in profile_links:
                                    href = link.get_attribute('href')
                                    if href:
                                        href = href.strip('/')
                                        if href.startswith('/'):
                                            href = href[1:]
                                        
                                        # Simple username pattern (just username, no other paths)
                                        if '/' not in href and len(href) > 0 and not any(skip in href.lower() for skip in ['search', 'hashtag', 'compose', 'home', 'explore', 'notifications', 'settings']):
                                            username = href
                                            break
                                
                                if username != 'unknown':
                                    break
                        
                        # Method 3: If we have username but no real tweet ID, try to find it again
                        if username != 'unknown' and not tweet_id.isdigit():
                            status_links = article.query_selector_all(f'a[href*="/{username}/status/"]')
                            for link in status_links:
                                href = link.get_attribute('href')
                                if href and f'/{username}/status/' in href:
                                    potential_id = href.split('/status/')[-1].split('?')[0].split('#')[0]
                                    if potential_id.isdigit():
                                        tweet_id = potential_id
                                        break
                        
                    except Exception as e:
                        pass
                    
                    # Try to get tweet ID from data attributes or aria-labels
                    if tweet_id.startswith('tweet_'):
                        try:
                            # Look for tweet timestamp links or data attributes
                            time_links = article.query_selector_all('a[href*="/status/"]')
                            for time_link in time_links:
                                href = time_link.get_attribute('href')
                                if href and '/status/' in href:
                                    tweet_id = href.split('/status/')[-1].split('?')[0]
                                    if tweet_id and tweet_id.isdigit():
                                        break
                        except:
                            pass
                        try:
                            # Look for tweet timestamp links or data attributes
                            time_links = article.query_selector_all('a[href*="/status/"]')
                            for time_link in time_links:
                                href = time_link.get_attribute('href')
                                if href and '/status/' in href:
                                    tweet_id = href.split('/status/')[-1].split('?')[0]
                                    if tweet_id and tweet_id.isdigit():
                                        break
                        except:
                            pass
                    
                    # Extract engagement metrics from HTML
                    likes = '0'
                    retweets = '0'
                    replies = '0'
                    
                    try:
                        # Try to extract engagement from aria-labels and data attributes
                        # Look for like button
                        like_button = article.query_selector('[data-testid="like"]')
                        if like_button:
                            aria_label = like_button.get_attribute('aria-label')
                            if aria_label:
                                # Parse "123 Likes" or "Like"
                                import re
                                match = re.search(r'(\d+)', aria_label)
                                if match:
                                    likes = match.group(1)
                        
                        # Look for retweet button
                        retweet_button = article.query_selector('[data-testid="retweet"]')
                        if retweet_button:
                            aria_label = retweet_button.get_attribute('aria-label')
                            if aria_label:
                                match = re.search(r'(\d+)', aria_label)
                                if match:
                                    retweets = match.group(1)
                        
                        # Look for reply button
                        reply_button = article.query_selector('[data-testid="reply"]')
                        if reply_button:
                            aria_label = reply_button.get_attribute('aria-label')
                            if aria_label:
                                match = re.search(r'(\d+)', aria_label)
                                if match:
                                    replies = match.group(1)
                    except Exception as e:
                        pass
                    
                    # Simple hashtag and mention extraction
                    import re
                    hashtags = ', '.join(re.findall(r'#\w+', text))
                    mentions = ', '.join(re.findall(r'@\w+', text))
                    
                    tweet = {
                        'tweet_id': tweet_id,
                        'tweet_url': f'https://x.com/{username}/status/{tweet_id}',
                        'username': username,
                        'display_name': username,
                        'verified': '',
                        'text': text,
                        'timestamp': '',
                        'language': '',
                        'tweet_type': 'original',
                        'likes': likes,
                        'retweets': retweets,
                        'replies': replies,
                        'quotes': '0',  # HTML extraction doesn't get quotes
                        'bookmarks': '0',  # HTML extraction doesn't get bookmarks
                        'views': '',  # HTML extraction doesn't get views
                        'engagement_rate': '',
                        'hashtags': hashtags,
                        'mentions': mentions,
                        'media_urls': '',
                        'is_original': 'true',
                        'tweet_link': f'https://x.com/{username}/status/{tweet_id}',
                        'profile_link': f'https://x.com/{username}',
                        'profile_bio': '',
                        'profile_location': '',
                        'profile_website': '',
                        'profile_email': '',
                        'followers_count': '0',
                        'following_count': '0'
                    }
                    
                    tweets.append(tweet)
                    
                except Exception as e:
                    continue
            
            print(f"Extracted {len(tweets)} tweets from current view")
            return tweets
            
        except Exception as e:
            print(f"Extract error: {e}")
            return tweets

    def build_url(self, keyword, hashtag, username, tweet_url, search_mode='top'):
        """Build search URL with engagement filtering
        
        Args:
            search_mode: 'top' (popular/high engagement), 'live' (latest), 'people' (from verified accounts)
        """
        if tweet_url:
            return tweet_url
        
        if username:
            return f'https://x.com/{username}'
        
    def build_url(self, keyword, hashtag, username, tweet_url, search_mode='top'):
        """Build search URL with engagement filtering
        
        Args:
            search_mode: 'top' (popular/high engagement), 'live' (latest), 'people' (from verified accounts)
        """
        if tweet_url:
            return tweet_url
        
        if username:
            return f'https://x.com/{username}'
        
        # Build search query - SIMPLIFIED APPROACH
        search_parts = []
        
        # Handle keywords - be more careful about formatting
        if keyword:
            # Clean up keyword input
            keyword_clean = keyword.strip()
            if keyword_clean:
                # If it contains commas, treat as multiple keywords
                if ',' in keyword_clean:
                    # Take only first keyword to avoid complex queries
                    first_keyword = keyword_clean.split(',')[0].strip()
                    if first_keyword:
                        search_parts.append(first_keyword)
                else:
                    search_parts.append(keyword_clean)
        
        # Handle hashtags - be more careful about formatting  
        if hashtag:
            hashtag_clean = hashtag.strip()
            if hashtag_clean:
                # If it contains commas, treat as multiple hashtags
                if ',' in hashtag_clean:
                    # Take only first hashtag to avoid complex queries
                    first_hashtag = hashtag_clean.split(',')[0].strip()
                    if first_hashtag and not first_hashtag.startswith('#'):
                        search_parts.append(f'#{first_hashtag}')
                    elif first_hashtag.startswith('#'):
                        search_parts.append(first_hashtag)
                else:
                    if not hashtag_clean.startswith('#'):
                        search_parts.append(f'#{hashtag_clean}')
                    else:
                        search_parts.append(hashtag_clean)
        
        if search_parts:
            # Create a simple, clean query
            combined_query = ' '.join(search_parts)
            
            # Add engagement filters for better results
            if search_mode == 'top':
                combined_query += ' min_faves:1'
            elif search_mode == 'people':
                combined_query += ' filter:verified'
            
            # Ensure query isn't too long (Twitter has limits)
            if len(combined_query) > 100:
                print(f"Query too long ({len(combined_query)} chars), using first part only")
                combined_query = search_parts[0] + ' min_faves:1'
            
            print(f"Search query: {combined_query}")
            encoded_query = quote(combined_query)
            
            # Choose the right filter parameter
            if search_mode == 'top':
                filter_param = 'f=top'
            elif search_mode == 'people':
                filter_param = 'f=user'
            else:
                filter_param = 'f=live'
            
            return f'https://x.com/search?q={encoded_query}&src=typed_query&{filter_param}'
        
        # Fallback to trending if no search terms
        return 'https://x.com/explore'

    def scrape_optimized(self, keyword='', hashtag='', username='', tweet_url='', num_tweets=500, search_mode='top'):
        """Optimized scraping method for very large targets (500+ tweets)
        
        Uses advanced strategies:
        - More aggressive scrolling
        - Query rotation
        - Enhanced tab management
        - Reduced delays
        """
        print(f"🚀 OPTIMIZED SCRAPING: Target {num_tweets} tweets")
        
        # Build search URL
        search_url = self.build_url(keyword, hashtag, username, tweet_url, search_mode)
        
        # Force optimal settings for large targets
        self.num_tabs = 12  # Maximum tabs
        self.csv_handler = FastCSVHandler(f"optimized_{num_tweets}")
        self.job_id = f"optimized_{num_tweets}"
        self.target_tweets = num_tweets
        
        print(f"OPTIMIZED SCRAPE: {self.num_tabs} parallel tabs")
        print(f"Target: {num_tweets} tweets")
        print(f"URL: {search_url}")
        
        # Reset counters
        self.total_scraped = 0
        self.target_reached = False
        
        # Enhanced parallel scraping with rotation
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=self.num_tabs) as executor:
            futures = []
            
            # Submit initial tasks
            for i in range(self.num_tabs):
                future = executor.submit(self._scrape_tab_optimized, search_url, num_tweets, i)
                futures.append(future)
                time.sleep(0.1)  # Stagger starts slightly
            
            # Monitor progress and rotate if needed
            completed = 0
            last_count = 0
            rotation_count = 0
            
            while completed < len(futures) and not self.target_reached:
                # Check for completed tasks
                for i, future in enumerate(futures):
                    if future.done() and future not in [f for f in futures[:completed]]:
                        try:
                            result = future.result()
                            print(f"Tab {i}: Completed with {result} tweets")
                        except Exception as e:
                            print(f"Tab {i}: Error - {e}")
                        completed += 1
                
                # Check if we should rotate stalled tabs
                current_time = time.time()
                if current_time - start_time > 60 * (rotation_count + 1):  # Every minute
                    current_count = self.total_scraped
                    if current_count == last_count and current_count < num_tweets * 0.8:
                        print(f"⚡ ROTATING tabs - progress stalled at {current_count}")
                        # Start new rotation tasks
                        for i in range(min(4, self.num_tabs)):  # Rotate up to 4 tabs
                            if rotation_count < 3:  # Max 3 rotations
                                future = executor.submit(self._scrape_tab_optimized, search_url, num_tweets, f"{i}_r{rotation_count}")
                                futures.append(future)
                        rotation_count += 1
                    last_count = current_count
                
                time.sleep(5)  # Check every 5 seconds
            
            # Wait for remaining tasks (with timeout)
            timeout = 300  # 5 minutes max
            for future in futures:
                try:
                    future.result(timeout=timeout)
                except:
                    pass
        
        return self.csv_handler.get_filename()

    def _scrape_tab_optimized(self, search_url, num_tweets, tab_id):
        """Optimized tab scraping with aggressive settings"""
        tab_tweets = 0
        browser = None
        
        try:
            # Launch browser
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = self._create_optimized_context(browser)
                page = context.new_page()
                
                # Set optimized timeouts
                page.set_default_navigation_timeout(15000)  # 15 seconds
                page.set_default_timeout(10000)  # 10 seconds
                
                print(f"Tab {tab_id}: Starting optimized scraping...")
                
                # Navigate
                response = page.goto(search_url, wait_until='domcontentloaded')
                print(f"Tab {tab_id}: Response status: {response.status}")
                
                if response.status != 200:
                    print(f"Tab {tab_id}: Bad response, skipping")
                    return 0
                
                # Wait for content with reduced timeout
                try:
                    page.wait_for_selector('[data-testid="tweet"]', timeout=10000)
                except:
                    print(f"Tab {tab_id}: No tweets found quickly, skipping")
                    return 0
                
                # Optimized scraping loop
                no_new_tweets = 0
                last_count = 0
                scroll_count = 0
                max_scrolls = 200  # Increased for large targets
                
                while (not self.target_reached and 
                       no_new_tweets < 10 and  # Reduced patience
                       scroll_count < max_scrolls):
                    
                    if self.total_scraped >= num_tweets:
                        self.target_reached = True
                        break
                    
                    # Fast extraction
                    new_tweets = self._extract_tweets_fast(page, tab_id)
                    tab_tweets += new_tweets
                    
                    if new_tweets > 0:
                        no_new_tweets = 0
                    else:
                        no_new_tweets += 1
                    
                    # Aggressive scrolling
                    page.evaluate("window.scrollBy(0, window.innerHeight * 2)")  # Double scroll
                    time.sleep(0.5)  # Faster scrolling
                    scroll_count += 1
                    
                    # Progress check
                    if scroll_count % 10 == 0:
                        progress = (self.total_scraped / num_tweets) * 100
                        print(f"Tab {tab_id}: Progress {progress:.1f}% ({self.total_scraped}/{num_tweets})")
                
                print(f"Tab {tab_id}: Finished with {tab_tweets} tweets")
                return tab_tweets
                
        except Exception as e:
            print(f"Tab {tab_id}: Error - {e}")
            return tab_tweets
        finally:
            if browser:
                browser.close()

    def _create_optimized_context(self, browser):
        """Create browser context optimized for speed"""
        context = browser.new_context(
            user_agent=random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            ]),
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={'Accept-Language': 'en-US,en;q=0.9'}
        )
        
        # Load cookies if available
        if hasattr(self, 'cookies') and self.cookies:
            context.add_cookies(self.cookies)
        
        return context

    def _extract_tweets_fast(self, page, tab_id):
        """Fast tweet extraction optimized for speed"""
        try:
            # Quick extraction
            tweets = page.query_selector_all('[data-testid="tweet"]')
            new_tweets = 0
            
            for tweet in tweets[-5:]:  # Only check last 5 tweets
                try:
                    tweet_data = self._extract_tweet_data_fast(tweet)
                    if tweet_data and not self._is_duplicate(tweet_data):
                        self.csv_handler.add_tweet(tweet_data)
                        self.total_scraped += 1
                        new_tweets += 1
                        
                        if self.total_scraped >= self.target_tweets:
                            self.target_reached = True
                            break
                except:
                    continue
            
            return new_tweets
        except:
            return 0

    def _extract_tweet_data_fast(self, tweet_element):
        """Fast tweet data extraction with minimal processing"""
        try:
            # Get basic data quickly
            text_elem = tweet_element.query_selector('[data-testid="tweetText"]')
            text = text_elem.inner_text() if text_elem else ""
            
            username_elem = tweet_element.query_selector('[data-testid="User-Name"] [href^="/"]')
            username = username_elem.get_attribute('href').strip('/') if username_elem else ""
            
            # Generate simple tweet data
            return {
                'username': username,
                'text': text[:500],  # Truncate for speed
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'likes': 1,  # Placeholder
                'retweets': 0,
                'replies': 0
            }
        except:
            return None

    def _scrape_bulk_urls(self, tweet_urls, job_id):
        """Handle bulk URL scraping"""
        print(f"📋 BULK MODE: {len(tweet_urls)} URLs")
        self.csv_handler = CSVHandler(job_id)
        
        for i, url in enumerate(tweet_urls):
            print(f"Scraping URL {i+1}/{len(tweet_urls)}: {url}")
            # Simple implementation for now
            time.sleep(1)
        
        return self.csv_handler.get_filename()