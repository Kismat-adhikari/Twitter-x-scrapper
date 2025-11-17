from playwright.sync_api import sync_playwright
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from scraper.proxy_manager import ProxyManager
from scraper.cookie_loader import load_cookies
from scraper.csv_handler import CSVHandler

class TwitterScraper:
    def __init__(self, num_tabs=4):
        self.num_tabs = num_tabs
        self.proxy_manager = ProxyManager()
        self.cookies = load_cookies()
        self.csv_handler = None
        self.user_data = None
        self.lock = threading.Lock()
        self.total_scraped = 0
    
    def scrape(self, keyword='', hashtag='', username='', tweet_url='', num_tweets=50, job_id=None):
        """Main scraping method with real-time CSV writing"""
        
        # Initialize CSV handler
        self.csv_handler = CSVHandler(job_id)
        self.scraping_username = username  # Store if we're scraping a user profile
        
        # Build search URL
        search_url = self.build_url(keyword, hashtag, username, tweet_url)
        
        print(f"🚀 Starting scrape with {self.num_tabs} parallel tabs...")
        print(f"🎯 Target: {num_tweets} tweets")
        print(f"🔗 URL: {search_url}")
        print(f"📝 Writing to: {self.csv_handler.tweets_file}")
        
        # Run parallel scraping
        tweets_per_tab = num_tweets  # Each tab tries to get the full amount
        
        with ThreadPoolExecutor(max_workers=self.num_tabs) as executor:
            futures = []
            
            for i in range(self.num_tabs):
                future = executor.submit(
                    self.scrape_tab,
                    search_url,
                    tweets_per_tab,
                    i
                )
                futures.append(future)
            
            # Wait for all tabs to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"❌ Tab error: {e}")
        
        # Get final count
        final_count = self.csv_handler.get_tweet_count()
        
        print(f"✅ Scraping complete! Collected {final_count} unique tweets (requested: {num_tweets})")
        
        if final_count > 0:
            filename = self.csv_handler.get_filename()
            print(f"📁 CSV saved: {filename}")
            return filename
        else:
            print("❌ No tweets collected")
            return None

    def build_url(self, keyword, hashtag, username, tweet_url):
        """Build Twitter search URL based on parameters"""
        from urllib.parse import quote
        
        if tweet_url:
            return tweet_url
        
        if username:
            return f'https://x.com/{username.lstrip("@")}'
        
        if hashtag:
            query = hashtag if hashtag.startswith('#') else f'#{hashtag}'
            encoded_query = quote(query)
            return f'https://x.com/search?q={encoded_query}&src=typed_query&f=live'
        
        if keyword:
            encoded_keyword = quote(keyword)
            return f'https://x.com/search?q={encoded_keyword}&src=typed_query&f=live'
        
        return 'https://x.com/home'
    
    def scrape_tab(self, url, target_tweets, tab_id):
        """Scrape tweets in a single browser tab"""
        proxy = self.proxy_manager.get_proxy()
        
        with sync_playwright() as p:
            try:
                # Launch browser with proxy
                browser = p.chromium.launch(
                    headless=False,
                    proxy=proxy
                )
                
                context = browser.new_context()
                
                # Add cookies for authentication
                if self.cookies:
                    context.add_cookies(self.cookies)
                
                page = context.new_page()
                
                print(f"Tab {tab_id}: Navigating to {url}")
                page.goto(url, timeout=60000)
                
                # Wait for page to load and tweets to appear
                time.sleep(5)
                
                # Try to close any popups/modals
                try:
                    close_button = page.query_selector('[aria-label="Close"]')
                    if close_button:
                        close_button.click()
                        time.sleep(1)
                except:
                    pass
                
                # If scraping a username, extract profile data (only first tab)
                if tab_id == 0 and self.scraping_username:
                    user_profile = self.scrape_user_profile(page, self.scraping_username)
                    self.csv_handler.save_user_profile(user_profile)
                
                scroll_attempts = 0
                max_scrolls = 30
                no_new_tweets_count = 0
                
                # Keep scrolling until we have enough tweets or run out
                while scroll_attempts < max_scrolls:
                    # Extract tweets from current view
                    new_tweets = self.extract_tweets(page, tab_id)
                    
                    # Write each tweet to CSV immediately
                    tweets_written = 0
                    for tweet in new_tweets:
                        # Try to append to CSV (will skip duplicates)
                        if self.csv_handler.append_tweet(tweet):
                            tweets_written += 1
                            
                            with self.lock:
                                self.total_scraped += 1
                                current_total = self.total_scraped
                            
                            # Check if we've reached target
                            if current_total >= target_tweets:
                                print(f"Tab {tab_id}: 🎯 Target reached! ({current_total}/{target_tweets})")
                                browser.close()
                                return
                    
                    if tweets_written > 0:
                        print(f"Tab {tab_id}: ✅ Wrote {tweets_written} new tweets to CSV (total: {self.total_scraped}/{target_tweets})")
                        no_new_tweets_count = 0
                    else:
                        no_new_tweets_count += 1
                        print(f"Tab {tab_id}: ⏳ No new tweets (attempt {no_new_tweets_count}/5)")
                        
                        # If no new tweets after 5 scrolls, stop
                        if no_new_tweets_count >= 5:
                            print(f"Tab {tab_id}: 🛑 Stopping - no new tweets after 5 attempts")
                            break
                    
                    # Scroll down to load more
                    page.evaluate('window.scrollBy(0, window.innerHeight * 2)')
                    time.sleep(2)
                    scroll_attempts += 1
                
                browser.close()
                print(f"Tab {tab_id}: ✅ Finished scraping")
                
            except Exception as e:
                import traceback
                print(f"Tab {tab_id} ❌ Error: {e}")
                traceback.print_exc()
                if proxy:
                    self.proxy_manager.mark_failed(proxy)
    
    def extract_tweets(self, page, tab_id):
        """Extract tweet data from page"""
        tweets = []
        
        try:
            # Wait for tweets to load
            page.wait_for_selector('article[data-testid="tweet"]', timeout=10000)
            
            # Get all tweet articles
            tweet_elements = page.query_selector_all('article[data-testid="tweet"]')
            print(f"Tab {tab_id}: 🔍 Found {len(tweet_elements)} tweet elements on page")
            
            for idx, element in enumerate(tweet_elements):
                try:
                    # Skip promoted tweets
                    promoted = element.query_selector('[data-testid="promotedIndicator"]')
                    if promoted:
                        print(f"Tab {tab_id}: 🚫 Skipping promoted tweet")
                        continue
                    
                    # Get text element first for later use
                    text_elem = element.query_selector('[data-testid="tweetText"]')
                    
                    # Check language - only accept English tweets (or undefined/null)
                    try:
                        if text_elem:
                            lang = text_elem.get_attribute('lang')
                            # Only skip if explicitly non-English (allow null/undefined)
                            if lang and lang not in ['en', 'und', 'qme', None]:
                                print(f"Tab {tab_id}: 🌐 Skipping non-English tweet (lang={lang})")
                                continue
                    except Exception as e:
                        # If language check fails, allow the tweet
                        pass
                    
                    # Skip replies - check for "Replying to @username" text in the tweet
                    try:
                        reply_indicator = element.inner_text()
                        if 'Replying to' in reply_indicator[:100]:  # Check first 100 chars
                            print(f"Tab {tab_id}: 💬 Skipping reply tweet")
                            continue
                    except:
                        pass
                    
                    # Skip retweets - check for retweet indicator
                    try:
                        retweet_indicator = element.query_selector('[data-testid="socialContext"]')
                        if retweet_indicator:
                            retweet_text = retweet_indicator.inner_text().lower()
                            if 'retweeted' in retweet_text or 'reposted' in retweet_text:
                                print(f"Tab {tab_id}: 🔄 Skipping retweet")
                                continue
                    except:
                        pass
                    
                    # Skip "Who to follow" and other recommendations
                    follow_button = element.query_selector('[data-testid*="follow"]')
                    if follow_button and not element.query_selector('[data-testid="tweetText"]'):
                        continue
                    
                    tweet_data = {}
                    
                    # Extract tweet ID from link (most reliable)
                    status_link = element.query_selector('a[href*="/status/"]')
                    if status_link:
                        href = status_link.get_attribute('href')
                        parts = href.split('/status/')
                        if len(parts) > 1:
                            tweet_id = parts[1].split('?')[0].split('/')[0]
                            tweet_data['tweet_id'] = tweet_id
                            
                            # Build full tweet URL
                            username = href.split('/')[1] if '/' in href else ''
                            tweet_data['tweet_url'] = f'https://x.com/{username}/status/{tweet_id}'
                            tweet_data['username'] = username
                        else:
                            continue
                    else:
                        continue
                    
                    # Extract tweet text (text_elem already retrieved above)
                    tweet_text = text_elem.inner_text() if text_elem else ''
                    
                    # Skip if no text (likely a retweet header or recommendation)
                    if not tweet_text or len(tweet_text.strip()) < 3:
                        print(f"Tab {tab_id}: ⚠️ Skipping tweet with no text")
                        continue
                    
                    # Additional check: Skip if tweet starts with "RT @" (manual retweet)
                    if tweet_text.strip().startswith('RT @'):
                        print(f"Tab {tab_id}: 🔄 Skipping manual retweet")
                        continue
                    
                    tweet_data['text'] = tweet_text
                    tweet_data['is_original'] = True  # Mark as original tweet
                    
                    # Store language (should be 'en' since we filtered)
                    tweet_data['language'] = text_elem.get_attribute('lang') if text_elem else 'en'
                    
                    # Extract display name (full name)
                    try:
                        user_name_elem = element.query_selector('[data-testid="User-Name"]')
                        if user_name_elem:
                            display_name_elem = user_name_elem.query_selector('span')
                            tweet_data['display_name'] = display_name_elem.inner_text() if display_name_elem else ''
                        else:
                            tweet_data['display_name'] = ''
                    except:
                        tweet_data['display_name'] = ''
                    
                    # Extract timestamp
                    time_elem = element.query_selector('time')
                    tweet_data['timestamp'] = time_elem.get_attribute('datetime') if time_elem else ''
                    
                    # Extract engagement metrics
                    tweet_data['replies'] = self.extract_metric(element, 'reply')
                    tweet_data['retweets'] = self.extract_metric(element, 'retweet')
                    tweet_data['likes'] = self.extract_metric(element, 'like')
                    
                    # Calculate engagement rate (if we have follower count, otherwise leave empty)
                    tweet_data['engagement_rate'] = ''  # Will be calculated if we scrape user profile
                    
                    # Extract hashtags from tweet text
                    hashtags = self.extract_hashtags(tweet_text)
                    tweet_data['hashtags'] = ', '.join(hashtags) if hashtags else ''
                    
                    # Extract mentions from tweet text
                    mentions = self.extract_mentions(tweet_text)
                    tweet_data['mentions'] = ', '.join(mentions) if mentions else ''
                    
                    # Extract media URLs
                    media_elements = element.query_selector_all('img[src*="media"]')
                    media_urls = [img.get_attribute('src') for img in media_elements if img.get_attribute('src')]
                    tweet_data['media_urls'] = ', '.join(media_urls) if media_urls else ''
                    
                    # Determine tweet type
                    tweet_data['tweet_type'] = self.determine_tweet_type(element, tweet_text)
                    
                    # Check if verified (blue checkmark)
                    verified_elem = element.query_selector('[data-testid="icon-verified"]')
                    tweet_data['verified'] = 'True' if verified_elem else 'False'
                    
                    tweets.append(tweet_data)
                    print(f"Tab {tab_id}: ✅ Extracted tweet: {tweet_text[:50]}...")
                
                except Exception as e:
                    import traceback
                    print(f"Tab {tab_id}: ❌ Error extracting tweet {idx}: {e}")
                    traceback.print_exc()
                    continue
        
        except Exception as e:
            print(f"Tab {tab_id}: Extract error: {e}")
        
        return tweets
    
    def extract_metric(self, element, metric_type):
        """Extract engagement metrics (likes, retweets, replies)"""
        try:
            metric_elem = element.query_selector(f'[data-testid="{metric_type}"]')
            if metric_elem:
                text = metric_elem.inner_text()
                # Handle K, M suffixes
                if 'K' in text:
                    return str(int(float(text.replace('K', '')) * 1000))
                elif 'M' in text:
                    return str(int(float(text.replace('M', '')) * 1000000))
                return text
        except:
            pass
        return '0'
    


    def is_relevant(self, tweet_text, username):
        """Check if tweet is relevant to the search query - LENIENT VERSION"""
        if not self.search_query:
            return True
        
        # Combine text and username for checking
        content = f"{tweet_text} {username}".lower()
        query_lower = self.search_query.lower().strip('#@')
        
        # Split query into individual search terms
        query_terms = [term.strip() for term in query_lower.replace(',', ' ').split() if term.strip()]
        
        # Check if ANY of the query terms match (even partial)
        for term in query_terms:
            if len(term) >= 3 and term in content:
                return True
        
        # Check for partial word matches (e.g., "game" matches "games", "gaming")
        for term in query_terms:
            if len(term) >= 4:
                # Check if term is part of any word in content
                content_words = content.split()
                for word in content_words:
                    if term in word or word in term:
                        return True
        
        # For AI-related searches, check for related terms
        ai_keywords = ['ai', 'artificial intelligence', 'ml', 'machine learning']
        if any(kw in query_lower for kw in ai_keywords):
            ai_terms = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning', 
                        'neural network', 'llm', 'gpt', 'chatgpt', 'openai', 'anthropic', 'claude',
                        'gemini', 'bard', 'copilot', 'midjourney', 'stable diffusion', 'generative',
                        'transformer', 'nlp', 'computer vision', 'reinforcement learning', 'pytorch',
                        'tensorflow', 'huggingface', 'langchain', 'rag', 'embedding', 'vector',
                        'model', 'training', 'dataset', 'algorithm']
            
            for term in ai_terms:
                if term in content:
                    return True
        
        # Very lenient: if we're on a search results page, trust Twitter's algorithm
        # Only filter out completely unrelated stuff
        return True

    def extract_hashtags(self, text):
        """Extract all hashtags from tweet text"""
        import re
        hashtags = re.findall(r'#\w+', text)
        return hashtags
    
    def extract_mentions(self, text):
        """Extract all @mentions from tweet text"""
        import re
        mentions = re.findall(r'@\w+', text)
        return mentions
    
    def determine_tweet_type(self, element, text):
        """Determine if tweet is original, quote, or thread_start"""
        # Check for quoted tweet
        quoted = element.query_selector('[data-testid="card.wrapper"]')
        if quoted:
            return 'quote'
        
        # Check for thread indicator (numbers like 1/5, 2/5, etc.)
        import re
        if re.search(r'\(\d+/\d+\)|\d+/\d+$', text):
            return 'thread_start'
        
        return 'original'
    
    def scrape_user_profile(self, username):
        """Scrape user profile data (bio, followers, etc.)"""
        proxy = self.proxy_manager.get_proxy()
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=False, proxy=proxy)
                context = browser.new_context()
                
                if self.cookies:
                    context.add_cookies(self.cookies)
                
                page = context.new_page()
                profile_url = f'https://x.com/{username.lstrip("@")}'
                
                print(f"📊 Scraping profile: {username}")
                page.goto(profile_url, timeout=60000)
                time.sleep(5)
                
                user_data = {
                    'username': username,
                    'display_name': '',
                    'bio': '',
                    'followers': '',
                    'following': '',
                    'total_tweets': '',
                    'verified': 'False'
                }
                
                # Extract display name
                try:
                    name_elem = page.query_selector('[data-testid="UserName"]')
                    if name_elem:
                        display_name = name_elem.query_selector('span')
                        user_data['display_name'] = display_name.inner_text() if display_name else ''
                except:
                    pass
                
                # Extract bio
                try:
                    bio_elem = page.query_selector('[data-testid="UserDescription"]')
                    user_data['bio'] = bio_elem.inner_text() if bio_elem else ''
                except:
                    pass
                
                # Extract follower/following counts
                try:
                    stats = page.query_selector_all('a[href*="/verified_followers"], a[href*="/following"]')
                    for stat in stats:
                        text = stat.inner_text().lower()
                        if 'follower' in text:
                            user_data['followers'] = text.split()[0]
                        elif 'following' in text:
                            user_data['following'] = text.split()[0]
                except:
                    pass
                
                # Extract total tweets
                try:
                    tweets_elem = page.query_selector('[data-testid="UserProfileHeader_Items"]')
                    if tweets_elem:
                        text = tweets_elem.inner_text()
                        import re
                        tweets_match = re.search(r'([\d,]+)\s+posts', text.lower())
                        if tweets_match:
                            user_data['total_tweets'] = tweets_match.group(1)
                except:
                    pass
                
                # Check verified status
                verified = page.query_selector('[data-testid="icon-verified"]')
                user_data['verified'] = 'True' if verified else 'False'
                
                browser.close()
                return user_data
                
            except Exception as e:
                print(f"❌ Error scraping profile {username}: {e}")
                return None

    def extract_hashtags(self, text):
        """Extract all hashtags from tweet text"""
        import re
        hashtags = re.findall(r'#\w+', text)
        return hashtags
    
    def extract_mentions(self, text):
        """Extract all @mentions from tweet text"""
        import re
        mentions = re.findall(r'@\w+', text)
        return mentions
    
    def determine_tweet_type(self, element, text):
        """Determine if tweet is original, quote, or thread_start"""
        # Check for quoted tweet
        quoted_tweet = element.query_selector('[data-testid="card.wrapper"]')
        if quoted_tweet:
            return 'quote'
        
        # Check for thread indicator (numbers like 1/5, 2/5)
        import re
        if re.search(r'\(\d+/\d+\)|\d+/\d+$', text):
            return 'thread_start'
        
        return 'original'

    def scrape_user_profile(self, page, username):
        """Scrape user profile data"""
        user_data = {
            'username': username,
            'display_name': '',
            'bio': '',
            'followers': '',
            'following': '',
            'total_tweets': '',
            'verified': 'False'
        }
        
        try:
            # Wait for profile to load
            time.sleep(3)
            
            # Extract display name
            try:
                name_elem = page.query_selector('[data-testid="UserName"]')
                if name_elem:
                    display_name = name_elem.query_selector('span')
                    user_data['display_name'] = display_name.inner_text() if display_name else ''
            except:
                pass
            
            # Extract bio
            try:
                bio_elem = page.query_selector('[data-testid="UserDescription"]')
                user_data['bio'] = bio_elem.inner_text() if bio_elem else ''
            except:
                pass
            
            # Extract follower/following counts
            try:
                # Look for links with "followers" and "following" text
                stats = page.query_selector_all('a[href*="/verified_followers"], a[href*="/following"]')
                for stat in stats:
                    text = stat.inner_text().lower()
                    if 'follower' in text:
                        # Extract number before "followers"
                        import re
                        match = re.search(r'([\d,\.]+[KMB]?)\s*follower', text, re.IGNORECASE)
                        if match:
                            user_data['followers'] = match.group(1)
                    elif 'following' in text:
                        match = re.search(r'([\d,\.]+[KMB]?)\s*following', text, re.IGNORECASE)
                        if match:
                            user_data['following'] = match.group(1)
            except:
                pass
            
            # Extract total tweets (posts)
            try:
                # Look for "posts" count
                posts_text = page.inner_text()
                import re
                match = re.search(r'([\d,\.]+[KMB]?)\s*posts', posts_text, re.IGNORECASE)
                if match:
                    user_data['total_tweets'] = match.group(1)
            except:
                pass
            
            # Check if verified
            try:
                verified = page.query_selector('[data-testid="icon-verified"]')
                user_data['verified'] = 'True' if verified else 'False'
            except:
                pass
            
            print(f"📊 User profile scraped: {user_data}")
            return user_data
            
        except Exception as e:
            print(f"❌ Error scraping user profile: {e}")
            return user_data

    def extract_metric(self, element, metric_type):
        """Extract engagement metrics (likes, retweets, replies)"""
        try:
            # Twitter uses data-testid for engagement buttons
            metric_elem = element.query_selector(f'[data-testid="{metric_type}"]')
            if metric_elem:
                # Get the text content
                text = metric_elem.inner_text().strip()
                
                # Handle empty (0 engagement)
                if not text or text == '':
                    return '0'
                
                # Handle K, M suffixes (e.g., "1.5K", "2M")
                if 'K' in text.upper():
                    number = text.upper().replace('K', '').strip()
                    try:
                        return str(int(float(number) * 1000))
                    except:
                        return text
                elif 'M' in text.upper():
                    number = text.upper().replace('M', '').strip()
                    try:
                        return str(int(float(number) * 1000000))
                    except:
                        return text
                
                # Return as-is if it's just a number
                return text.replace(',', '')
            
            return '0'
        except Exception as e:
            return '0'
