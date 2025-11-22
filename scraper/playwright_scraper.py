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
        
        # Balanced tab count for speed + stability
        if self.num_tabs is None:
            if num_tweets >= 200:
                self.num_tabs = 6  # High for very large targets
            elif num_tweets >= 100:
                self.num_tabs = 5  # Medium-high for large targets
            elif num_tweets >= 50:
                self.num_tabs = 4  # Standard for medium targets
            else:
                self.num_tabs = 3  # Conservative for small targets
        
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
                            self._process_api_entry(entry, tab_id)
            
            # Also check for direct tweet data
            tweets = self._find_in_dict(data, 'tweets')
            if tweets and isinstance(tweets, dict):
                for tweet_id, tweet_data in tweets.items():
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
            
            # FILTER: Only include tweets with engagement > 0
            if likes == 0 and retweets == 0 and replies == 0:
                return
            
            # Get user data - try ALL possible paths in the API response
            username = None
            display_name = None
            verified = False
            
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
                'views': '',  # Views not always available in API
                'engagement_rate': '',
                'hashtags': hashtags,
                'mentions': mentions,
                'media_urls': media_urls,
                'is_original': 'true',
                'tweet_link': f'https://x.com/{username}/status/{tweet_id}',
                'profile_link': f'https://x.com/{username}'
            }
            
            # Add to CSV if unique and has engagement
            if self.csv_handler and self.csv_handler.add_tweet(tweet):
                with self.lock:
                    self.total_scraped += 1
                current_count = self.csv_handler.get_tweet_count()
                print(f"Tab {tab_id}: API tweet - {username}: {likes} likes, {retweets} RTs, {replies} replies (Total: {current_count})")
        
        except Exception as e:
            pass

    def scrape_tab_simple(self, search_url, num_tweets, tab_id):
        """Simplified, more reliable tab scraping"""
        print(f"Tab {tab_id}: Starting...")
        
        try:
            with sync_playwright() as p:
                # Launch browser with minimal flags
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                context = browser.new_context()
                if self.cookies:
                    context.add_cookies(self.cookies)
                
                page = context.new_page()
                
                # Set up API response interception for real engagement metrics
                if self.use_api_extraction:
                    page.on('response', lambda response: self._intercept_api_response(response, tab_id))
                
                # Navigate to URL
                print(f"Tab {tab_id}: Navigating to search page...")
                page.goto(search_url, timeout=30000)
                time.sleep(random.uniform(1, 2))  # Faster initial wait
                
                # Debug: Check what we loaded
                title = page.title()
                print(f"Tab {tab_id}: Page title: {title}")
                
                # Check if we're on the right page
                if title == "X" or "login" in title.lower() or "sign" in title.lower():
                    print(f"Tab {tab_id}: Authentication required or blocked, trying to navigate to X.com first")
                    # Try going to main page first
                    page.goto("https://x.com", timeout=30000)
                    time.sleep(random.uniform(2, 3))
                    
                    # Now try search again
                    page.goto(search_url, timeout=30000)
                    time.sleep(random.uniform(1, 2))
                    
                    new_title = page.title()
                    print(f"Tab {tab_id}: After retry, page title: {new_title}")
                    
                    # If still blocked, skip this tab
                    if new_title == "X" or "login" in new_title.lower():
                        print(f"Tab {tab_id}: Still blocked, skipping this tab")
                        return
                
                # Try to close any popups
                try:
                    close_btn = page.query_selector('[aria-label=\"Close\"]')
                    if close_btn:
                        close_btn.click()
                        time.sleep(1)
                except:
                    pass
                
                tweets_found = 0
                max_scrolls = 150 if num_tweets >= 200 else (80 if num_tweets >= 100 else 30)  # Much more for 200+ tweets
                no_content_count = 0
                
                for scroll in range(max_scrolls):
                    if self.target_reached:
                        print(f"Tab {tab_id}: Target reached globally, stopping")
                        break
                    
                    # Extract tweets from current view
                    tweets = self.extract_tweets_simple(page)
                    
                    # Check if we're on a "no results" page
                    try:
                        page_content = page.content().lower()
                        if 'no results' in page_content or 'try searching for something else' in page_content:
                            print(f"Tab {tab_id}: No results page detected, stopping")
                            break
                    except:
                        # If page content check fails, continue
                        pass
                    
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
                    
                    # More reasonable persistence for large targets
                    current_total = self.csv_handler.get_tweet_count()
                    progress_ratio = current_total / num_tweets
                    
                    if num_tweets >= 200:
                        # For very large targets (200+), be reasonably persistent
                        if progress_ratio < 0.3:
                            max_no_content = 10  # Persistent early on
                        elif progress_ratio < 0.7:
                            max_no_content = 8   # Medium mid-way
                        else:
                            max_no_content = 6   # Faster near end
                    elif num_tweets >= 100:
                        # For large targets (100-199), balanced persistence
                        if progress_ratio < 0.5:
                            max_no_content = 8   # Persistent early on
                        elif progress_ratio < 0.8:
                            max_no_content = 6   # Medium mid-way
                        else:
                            max_no_content = 5   # Faster near end
                    else:
                        max_no_content = 6
                    
                    if no_content_count >= max_no_content:
                        print(f"Tab {tab_id}: No new content for {max_no_content} attempts (progress: {progress_ratio:.1%}), stopping")
                        break
                    
                    # Aggressive scrolling for maximum speed
                    scroll_multiplier = 6 if num_tweets >= 200 else (5 if num_tweets >= 100 else 4)
                    page.evaluate(f'window.scrollBy(0, window.innerHeight * {scroll_multiplier})')
                    
                    # Balanced fast wait times for speed + stability
                    if no_content_count >= 5:
                        sleep_time = random.uniform(2.0, 3.0)  # Reasonable wait when struggling
                    elif no_content_count >= 3:
                        sleep_time = random.uniform(1.5, 2.0)  # Medium wait when struggling  
                    elif num_tweets >= 200:
                        sleep_time = random.uniform(1.0, 1.5)  # Fast for very large targets
                    elif num_tweets >= 100:
                        sleep_time = random.uniform(0.8, 1.2)  # Fast for large targets
                    else:
                        sleep_time = random.uniform(0.6, 1.0)  # Fast for small targets
                    
                    time.sleep(sleep_time)
                
                print(f"Tab {tab_id}: Finished with {tweets_found} tweets")
                browser.close()
                
        except Exception as e:
            print(f"Tab {tab_id}: Error: {e}")

    def extract_tweets_simple(self, page):
        """Simplified tweet extraction with basic selectors"""
        tweets = []
        
        try:
            # Moderate content loading
            time.sleep(0.3)
            
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
                        'profile_link': f'https://x.com/{username}'
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
        
        # Build combined search query
        search_parts = []
        
        if keyword:
            search_parts.append(keyword)
            
        if hashtag:
            # Handle multiple hashtags separated by commas
            hashtag_parts = [tag.strip() for tag in hashtag.split(',') if tag.strip()]
            for tag in hashtag_parts:
                # Add # if not already present
                if not tag.startswith('#'):
                    search_parts.append(f'#{tag}')
                else:
                    search_parts.append(tag)
        
        if search_parts:
            combined_query = ' '.join(search_parts)
            
            # Add engagement filters to the query for better results
            # These filters help ensure tweets have actual engagement
            if search_mode == 'top':
                # Add minimum engagement filter (at least 10 likes)
                combined_query += ' min_faves:10'
            elif search_mode == 'people':
                # Filter for verified accounts only
                combined_query += ' filter:verified'
            
            # For very complex queries, try a simpler approach
            # But be more permissive for hashtag-heavy searches
            hashtag_count = combined_query.count('#')
            keyword_complexity = len(keyword.split(',')) if keyword else 1
            
            # Only simplify if it's REALLY complex (many keywords + many hashtags)
            if (len(combined_query) > 80 or 
                (keyword_complexity > 3 and hashtag_count > 4) or
                combined_query.count(',') > 6):
                print(f"Very complex query detected, simplifying: {combined_query}")
                # For hashtag-heavy searches, keep more hashtags
                simple_parts = []
                if keyword:
                    # Take first 2 keywords instead of 1
                    keywords = [k.strip() for k in keyword.split(',')][:2]
                    simple_parts.extend(keywords)
                if hashtag:
                    # Take first 4 hashtags instead of 1
                    hashtags = [tag.strip() for tag in hashtag.split(',')][:4]
                    for tag in hashtags:
                        if not tag.startswith('#'):
                            simple_parts.append(f'#{tag}')
                        else:
                            simple_parts.append(tag)
                combined_query = ' '.join(simple_parts)
                
                # Re-add engagement filter after simplification
                if search_mode == 'top':
                    combined_query += ' min_faves:10'
                elif search_mode == 'people':
                    combined_query += ' filter:verified'
                
                print(f"Simplified to: {combined_query}")
            
            encoded_query = quote(combined_query)
            
            # Choose the right filter parameter
            if search_mode == 'top':
                filter_param = 'f=top'  # Top/Popular tweets (ranked by engagement)
            elif search_mode == 'people':
                filter_param = 'f=user'  # From people (verified accounts)
            else:
                filter_param = 'f=live'  # Latest tweets (chronological)
            
            return f'https://x.com/search?q={encoded_query}&src=typed_query&{filter_param}'
        
        return 'https://x.com/home'

    def _scrape_bulk_urls(self, tweet_urls, job_id):
        """Handle bulk URL scraping"""
        print(f"📋 BULK MODE: {len(tweet_urls)} URLs")
        self.csv_handler = CSVHandler(job_id)
        
        for i, url in enumerate(tweet_urls):
            print(f"Scraping URL {i+1}/{len(tweet_urls)}: {url}")
            # Simple implementation for now
            time.sleep(1)
        
        return self.csv_handler.get_filename()