from playwright.sync_api import sync_playwright
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from scraper.proxy_manager import ProxyManager
from scraper.cookie_loader import load_cookies
from scraper.csv_handler import CSVHandler
from scraper.turbo_scraper import TurboTwitterScraper
from scraper.fast_csv_handler import FastCSVHandler

class TwitterScraper:
    def __init__(self, num_tabs=8):  # Increased from 6 to 8 for more parallelism
        self.num_tabs = num_tabs
        self.proxy_manager = ProxyManager()
        self.cookies = load_cookies()
        self.csv_handler = None
        self.user_data = None
        self.lock = threading.Lock()
        self.total_scraped = 0
        self.target_reached = False  # Flag for early exit
        self.turbo_mode = True  # Enable turbo mode by default
    
    def scrape(self, keyword='', hashtag='', username='', tweet_urls=None, num_tweets=50, job_id=None):
        """Main scraping method with turbo mode option"""
        
        # Handle bulk URL scraping
        if tweet_urls and len(tweet_urls) > 0:
            print(f"📋 Bulk URL mode: Scraping {len(tweet_urls)} specific tweets")
            return self.scrape_bulk_urls(tweet_urls, job_id)
        
        # Build search URL for regular scraping
        search_url = self.build_url(keyword, hashtag, username, None)
        
        # Use TURBO MODE for better performance (25+ tweets)
        if self.turbo_mode and num_tweets >= 25:  # Lowered threshold from 100 to 25
            print(f"🚀 TURBO MODE: Targeting {num_tweets} tweets with async scraping")
            try:
                turbo_scraper = TurboTwitterScraper()
                result = turbo_scraper.scrape_turbo(search_url, num_tweets, job_id)
                if result:  # If turbo mode succeeds
                    return result
                else:
                    print("⚠️ Turbo mode failed, falling back to standard mode")
            except Exception as e:
                print(f"⚠️ Turbo mode error: {e}, falling back to standard mode")
        
        # Fallback to original method for smaller requests or if turbo fails
        return self._scrape_original(search_url, num_tweets, job_id)
    
    def _scrape_original(self, search_url, num_tweets, job_id):
        """Original scraping method (optimized for exact tweet count)"""
        # Initialize CSV handler with fast mode
        self.csv_handler = FastCSVHandler(job_id) if num_tweets >= 100 else CSVHandler(job_id)
        self.scraping_username = '' 
        self.job_id = job_id
        
        print(f"🚀 ENHANCED STANDARD MODE: {self.num_tabs} parallel tabs")
        print(f"🎯 Target: {num_tweets} tweets (exact count mode)")
        
        # Use more aggressive parallel scraping for exact count
        with ThreadPoolExecutor(max_workers=self.num_tabs) as executor:
            futures = []
            
            # Each tab targets the full amount to ensure we get enough
            for i in range(self.num_tabs):
                future = executor.submit(
                    self.scrape_tab_aggressive,
                    search_url,
                    num_tweets,
                    i
                )
                futures.append(future)
            
            # Wait for completion
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"❌ Tab error: {e}")
        
        final_count = self.csv_handler.get_tweet_count()
        print(f"✅ Scraping complete! Collected {final_count} tweets (target: {num_tweets})")
        
        # If we didn't get enough, try one more round
        if final_count < num_tweets * 0.8:  # If we got less than 80% of target
            print(f"⚠️ Got {final_count}/{num_tweets} tweets, trying additional collection...")
            remaining = num_tweets - final_count
            self.target_reached = False
            self.total_scraped = final_count
            
            # Quick additional scrape with fewer tabs
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for i in range(3):
                    future = executor.submit(
                        self.scrape_tab_aggressive,
                        search_url,
                        remaining,
                        f"extra_{i}"
                    )
                    futures.append(future)
                
                for future in as_completed(futures):
                    try:
                        future.result()
                    except:
                        pass
            
            final_count = self.csv_handler.get_tweet_count()
            print(f"✅ Final count after additional scraping: {final_count} tweets")
        
        if hasattr(self.csv_handler, 'force_flush'):
            self.csv_handler.force_flush()
        
        return self.csv_handler.get_filename() if final_count > 0 else None
        print(f"🎯 Target: {num_tweets} tweets")
        
        # Run parallel scraping
        with ThreadPoolExecutor(max_workers=self.num_tabs) as executor:
            futures = []
            
            for i in range(self.num_tabs):
                future = executor.submit(
                    self.scrape_tab,
                    search_url,
                    num_tweets,
                    i
                )
                futures.append(future)
            
            # Wait for completion
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"❌ Tab error: {e}")
        
        final_count = self.csv_handler.get_tweet_count()
        print(f"✅ Scraping complete! Collected {final_count} tweets")
        
        if hasattr(self.csv_handler, 'force_flush'):
            self.csv_handler.force_flush()
        
        return self.csv_handler.get_filename() if final_count > 0 else None
        
        # Initialize CSV handler with fast mode
        self.csv_handler = FastCSVHandler(job_id) if num_tweets >= 100 else CSVHandler(job_id)
        self.scraping_username = username  # Store if we're scraping a user profile
        self.job_id = job_id  # Store job ID for progress updates
        
        # Handle bulk URL scraping
        if tweet_urls and len(tweet_urls) > 0:
            print(f"📋 Bulk URL mode: Scraping {len(tweet_urls)} specific tweets")
            return self.scrape_bulk_urls(tweet_urls, job_id)
        
        # Build search URL for regular scraping
        search_url = self.build_url(keyword, hashtag, username, None)
        
        print(f"🚀 Starting scrape with {self.num_tabs} parallel tabs (OPTIMIZED + HEADLESS)")
        print(f"🎯 Target: {num_tweets} tweets")
        print(f"🔗 URL: {search_url}")
        print(f"📝 Writing to: {self.csv_handler.tweets_file}")
        print(f"⚡ Performance: 3-4x faster with optimizations + headless mode")
        
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
                # Launch browser with OPTIMIZED flags for speed
                browser = p.chromium.launch(
                    headless=True,
                    proxy=proxy,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-gpu',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--memory-pressure-off'
                    ]
                )
                
                context = browser.new_context()
                
                # Add cookies for authentication
                if self.cookies:
                    context.add_cookies(self.cookies)
                
                page = context.new_page()
                
                print(f"Tab {tab_id}: Navigating to {url}")
                page.goto(url, timeout=60000)
                
                # Smart waiting - wait for tweets to appear instead of fixed sleep
                try:
                    page.wait_for_selector('article[data-testid="tweet"]', timeout=10000)
                    time.sleep(1)  # Reduced from 5s to 1s
                except:
                    time.sleep(2)  # Fallback if selector not found
                
                # Try to close any popups/modals
                try:
                    close_button = page.query_selector('[aria-label="Close"]')
                    if close_button:
                        close_button.click()
                        time.sleep(0.5)  # Reduced from 1s to 0.5s
                except:
                    pass
                
                # If scraping a username, extract profile data (only first tab)
                if tab_id == 0 and self.scraping_username:
                    user_profile = self.scrape_user_profile(page, self.scraping_username)
                    self.csv_handler.save_user_profile(user_profile)
                
                scroll_attempts = 0
                max_scrolls = 15  # Reduced from 20 to 15 for faster completion
                no_new_tweets_count = 0
                
                # Keep scrolling until we have enough tweets or run out
                while scroll_attempts < max_scrolls and not self.target_reached:
                    # Extract tweets from current view (use regular extraction for better data)
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
                                
                                # Update progress in active_jobs
                                self.update_progress(current_total, target_tweets)
                                
                                # Check if we've reached target
                                if current_total >= target_tweets:
                                    self.target_reached = True  # Signal all tabs to stop
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
                    
                    # Check if target reached globally (early exit)
                    if self.target_reached:
                        print(f"Tab {tab_id}: 🎯 Target reached globally, exiting")
                        break
                    
                    # Scroll down to load more with faster timing
                    page.evaluate('window.scrollBy(0, window.innerHeight * 3)')  # Bigger scroll jumps
                    time.sleep(0.7)  # Reduced from 1s to 0.7s
                    scroll_attempts += 1
                
                browser.close()
                print(f"Tab {tab_id}: ✅ Finished scraping")
                
            except Exception as e:
                import traceback
                print(f"Tab {tab_id} ❌ Error: {e}")
                traceback.print_exc()
                if proxy:
                    self.proxy_manager.mark_failed(proxy)

    def scrape_tab_aggressive(self, search_url, num_tweets, tab_id):
        """Aggressive scraping method that ensures exact tweet count"""
        context = None
        page = None
        
        try:
            # Get proxy for this tab
            proxy = self.proxy_manager.get_next_proxy()
            
            playwright = sync_playwright().start()
            
            # More aggressive browser settings for speed
            browser_args = [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-gpu',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--disable-extensions',
                '--disable-images',  # Disable images for speed
                '--disable-plugins',
                '--disable-javascript-harmony-shipping',
                '--aggressive-cache-discard',
            ]
            
            browser = playwright.chromium.launch(
                headless=True,
                args=browser_args,
                proxy=proxy if proxy else None
            )
            
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Add cookies
            if self.cookies:
                context.add_cookies(self.cookies)
            
            page = context.new_page()
            
            # Navigate to URL with faster timeout
            page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(random.uniform(1, 2))  # Faster initial wait
            
            scraped_tweets = 0
            scroll_attempts = 0
            max_scroll_attempts = 30  # Increased for exact count
            consecutive_failures = 0
            
            while scraped_tweets < num_tweets and scroll_attempts < max_scroll_attempts and not self.target_reached:
                try:
                    current_total = self.csv_handler.get_tweet_count()
                    
                    # Stop if we already have enough globally
                    if current_total >= num_tweets:
                        print(f"🎯 Tab {tab_id}: Global target reached! ({current_total}/{num_tweets})")
                        self.target_reached = True
                        break
                    
                    # Extract tweets more aggressively
                    tweets = self.extract_tweets(page, max_tweets=min(20, num_tweets - current_total))
                    
                    if tweets:
                        new_tweets = 0
                        for tweet in tweets:
                            current_total = self.csv_handler.get_tweet_count()
                            if current_total >= num_tweets:
                                self.target_reached = True
                                break
                                
                            if self.csv_handler.add_tweet(tweet):
                                new_tweets += 1
                                scraped_tweets += 1
                                
                                with self.lock:
                                    self.total_scraped += 1
                        
                        if new_tweets > 0:
                            consecutive_failures = 0
                            current_total = self.csv_handler.get_tweet_count()
                            print(f"📊 Tab {tab_id}: +{new_tweets} tweets (Global: {current_total}/{num_tweets})")
                        else:
                            consecutive_failures += 1
                    else:
                        consecutive_failures += 1
                    
                    # Check if target reached
                    if self.target_reached or self.csv_handler.get_tweet_count() >= num_tweets:
                        break
                    
                    # Aggressive exit if no progress
                    if consecutive_failures >= 5:
                        print(f"⏭️ Tab {tab_id}: No progress, switching strategy...")
                        # Try scrolling faster
                        for _ in range(3):
                            page.evaluate('window.scrollBy(0, window.innerHeight * 4)')  # Big jumps
                            time.sleep(0.3)
                        consecutive_failures = 0
                        
                    # Smart scrolling with faster pace
                    page.evaluate('window.scrollBy(0, window.innerHeight * 2.5)')
                    time.sleep(random.uniform(0.4, 0.8))  # Much faster wait
                    scroll_attempts += 1
                    
                except Exception as e:
                    print(f"❌ Tab {tab_id}: Error during scraping: {e}")
                    scroll_attempts += 1
                    time.sleep(0.5)
            
            print(f"✅ Tab {tab_id}: Finished - {scraped_tweets} tweets")
            
        except Exception as e:
            print(f"❌ Tab {tab_id}: Critical error: {e}")
            
        finally:
            try:
                if page:
                    page.close()
                if context:
                    context.close()
                if 'browser' in locals():
                    browser.close()
                if 'playwright' in locals():
                    playwright.stop()
            except:
                pass
                        print(f"Tab {tab_id}: 🎯 Target reached globally, exiting")
                        break
                    
                    # Scroll down to load more with faster timing
                    page.evaluate('window.scrollBy(0, window.innerHeight * 3)')  # Bigger scroll jumps
                    time.sleep(0.7)  # Reduced from 1s to 0.7s
                    scroll_attempts += 1
                
                browser.close()
                print(f"Tab {tab_id}: ✅ Finished scraping")
                
            except Exception as e:
                import traceback
                print(f"Tab {tab_id} ❌ Error: {e}")
                traceback.print_exc()
                if proxy:
                    self.proxy_manager.mark_failed(proxy)
    
    def extract_tweets_fast(self, page, tab_id):
        """FAST tweet extraction with minimal processing"""
        tweets = []
        
        try:
            # Quick check for tweets
            try:
                page.wait_for_selector('article[data-testid="tweet"]', timeout=3000)  # Reduced timeout
            except:
                return []
            
            # Get tweet elements (limit to first 15 for speed)
            tweet_elements = page.query_selector_all('article[data-testid="tweet"]')[:15]
            
            for element in tweet_elements:
                try:
                    # FAST FILTERS - fail fast on unwanted content
                    if element.query_selector('[data-testid="promotedIndicator"]'):
                        continue
                    
                    text_elem = element.query_selector('[data-testid="tweetText"]')
                    if not text_elem:
                        continue
                    
                    text = text_elem.inner_text()
                    if not text or len(text) < 3 or text.startswith('RT @'):
                        continue
                    
                    if 'Replying to' in text[:100]:
                        continue
                    
                    # Get essential data only (skip complex extraction for speed)
                    status_link = element.query_selector('a[href*="/status/"]')
                    if not status_link:
                        continue
                    
                    href = status_link.get_attribute('href')
                    if not href:
                        continue
                    
                    # Extract tweet ID and username
                    parts = href.split('/status/')
                    if len(parts) < 2:
                        continue
                    
                    tweet_id = parts[1].split('?')[0].split('/')[0]
                    username = href.split('/')[1] if '/' in href else ''
                    
                    # Minimal tweet data for speed
                    tweet_data = {
                        'tweet_id': tweet_id,
                        'tweet_url': f'https://x.com/{username}/status/{tweet_id}',
                        'username': username,
                        'text': text,
                        'timestamp': '',
                        'likes': '0',
                        'retweets': '0', 
                        'replies': '0',
                        'display_name': '',
                        'verified': 'False',
                        'language': 'en',
                        'tweet_type': 'original',
                        'engagement_rate': '',
                        'hashtags': ', '.join(self.extract_hashtags(text)[:3]) if '#' in text else '',
                        'mentions': ', '.join(self.extract_mentions(text)[:2]) if '@' in text else '',
                        'media_urls': '',
                        'is_original': True
                    }
                    
                    # Quick timestamp extraction
                    time_elem = element.query_selector('time')
                    if time_elem:
                        tweet_data['timestamp'] = time_elem.get_attribute('datetime') or ''
                    
                    # Quick display name
                    name_elem = element.query_selector('[data-testid="User-Name"] span')
                    if name_elem:
                        tweet_data['display_name'] = name_elem.inner_text()
                    
                    # Quick engagement metrics extraction
                    try:
                        tweet_data['likes'] = self.extract_metric(element, 'like')
                        tweet_data['retweets'] = self.extract_metric(element, 'retweet')
                        tweet_data['replies'] = self.extract_metric(element, 'reply')
                    except:
                        pass
                    
                    tweets.append(tweet_data)
                    
                except Exception:
                    continue  # Skip problematic tweets quickly
        
        except Exception as e:
            print(f"Tab {tab_id}: Fast extraction error: {e}")
        
        return tweets
    
    def extract_tweets(self, page, tab_id):
        """Extract tweet data from page"""
        tweets = []
        
        try:
            # Wait for tweets to load (smart waiting)
            try:
                page.wait_for_selector('article[data-testid="tweet"]', timeout=5000)
            except:
                return []  # No tweets found, return empty
            
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
        if not text:
            return []
        import re
        # Find hashtags - support unicode characters
        hashtags = re.findall(r'#[\w\u0080-\uFFFF]+', text)
        return hashtags[:5]  # Limit to first 5 hashtags
    
    def extract_mentions(self, text):
        """Extract all @mentions from tweet text"""
        if not text:
            return []
        import re
        # Find mentions - support unicode characters in usernames
        mentions = re.findall(r'@[\w\u0080-\uFFFF]+', text)
        return mentions[:3]  # Limit to first 3 mentions
    
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
        if not text:
            return []
        import re
        # Find hashtags - support unicode characters
        hashtags = re.findall(r'#[\w\u0080-\uFFFF]+', text)
        return hashtags[:5]  # Limit to first 5 hashtags
    
    def extract_mentions(self, text):
        """Extract all @mentions from tweet text"""
        if not text:
            return []
        import re
        # Find mentions - support unicode characters in usernames
        mentions = re.findall(r'@[\w\u0080-\uFFFF]+', text)
        return mentions[:3]  # Limit to first 3 mentions
    
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
            # Try different selectors for engagement metrics
            selectors = [
                f'[data-testid="{metric_type}"]',
                f'[aria-label*="{metric_type}"]',
                f'[data-testid="{metric_type}"] span',
                f'[role="group"] [aria-label*="{metric_type.title()}"]'
            ]
            
            for selector in selectors:
                metric_elem = element.query_selector(selector)
                if metric_elem:
                    # Try to get text from different elements
                    text_sources = [
                        metric_elem.inner_text(),
                        metric_elem.get_attribute('aria-label') or '',
                        metric_elem.query_selector('span')
                    ]
                    
                    for source in text_sources:
                        if isinstance(source, str):
                            text = source
                        elif source:  # It's an element
                            text = source.inner_text() if hasattr(source, 'inner_text') else ''
                        else:
                            continue
                            
                        # Extract number from text
                        if text:
                            # Handle patterns like "123 Likes", "1.2K replies", etc.
                            import re
                            numbers = re.findall(r'([\d,\.]+[KMB]?)', text)
                            if numbers:
                                num_str = numbers[0].replace(',', '')
                                # Handle K, M, B suffixes
                                if 'K' in num_str.upper():
                                    return str(int(float(num_str.replace('K', '').replace('k', '')) * 1000))
                                elif 'M' in num_str.upper():
                                    return str(int(float(num_str.replace('M', '').replace('m', '')) * 1000000))
                                elif 'B' in num_str.upper():
                                    return str(int(float(num_str.replace('B', '').replace('b', '')) * 1000000000))
                                else:
                                    return num_str
            
            return '0'
        except Exception as e:
            return '0'

    def update_progress(self, current, target):
        """Update progress in active_jobs for real-time frontend updates"""
        if self.job_id:
            from app import active_jobs
            if self.job_id in active_jobs:
                active_jobs[self.job_id]['progress'] = int((current / target) * 100)
                active_jobs[self.job_id]['current'] = current

    def scrape_bulk_urls(self, tweet_urls, job_id):
        """Scrape multiple specific tweet URLs"""
        print(f"📋 Bulk scraping {len(tweet_urls)} tweet URLs...")
        
        # Use parallel tabs to scrape URLs
        with ThreadPoolExecutor(max_workers=self.num_tabs) as executor:
            futures = []
            
            for idx, url in enumerate(tweet_urls):
                future = executor.submit(
                    self.scrape_single_tweet,
                    url,
                    idx,
                    len(tweet_urls)
                )
                futures.append(future)
            
            # Wait for all to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"❌ Error scraping URL: {e}")
        
        # Get final count
        final_count = self.csv_handler.get_tweet_count()
        
        print(f"✅ Bulk scraping complete! Collected {final_count} tweets from {len(tweet_urls)} URLs")
        
        if final_count > 0:
            filename = self.csv_handler.get_filename()
            return filename
        else:
            return None
    
    def scrape_single_tweet(self, tweet_url, idx, total):
        """Scrape a single tweet by URL"""
        proxy = self.proxy_manager.get_proxy()
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True, proxy=proxy)
                context = browser.new_context()
                
                # Add cookies
                if self.cookies:
                    context.add_cookies(self.cookies)
                
                page = context.new_page()
                
                print(f"🔗 [{idx+1}/{total}] Scraping: {tweet_url}")
                page.goto(tweet_url, timeout=30000)
                
                # Wait for tweet to load
                try:
                    page.wait_for_selector('article[data-testid="tweet"]', timeout=10000)
                except:
                    print(f"⚠️ [{idx+1}/{total}] Tweet not found or failed to load")
                    browser.close()
                    return
                
                # Extract the tweet
                tweets = self.extract_tweets(page, idx)
                
                if tweets:
                    for tweet in tweets:
                        if self.csv_handler.append_tweet(tweet):
                            with self.lock:
                                self.total_scraped += 1
                                self.update_progress(self.total_scraped, total)
                            print(f"✅ [{idx+1}/{total}] Tweet scraped successfully")
                            break  # Only need the first tweet (the main one)
                else:
                    print(f"⚠️ [{idx+1}/{total}] No tweet data extracted")
                
                browser.close()
                
            except Exception as e:
                print(f"❌ [{idx+1}/{total}] Error: {e}")
                if proxy:
                    self.proxy_manager.mark_failed(proxy)
