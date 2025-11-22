"""
Clean optimized scraper for exact tweet count delivery
"""
import os
import csv
import time
import random
import threading
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
from scraper.proxy_manager import ProxyManager
from scraper.csv_handler import CSVHandler
from scraper.fast_csv_handler import FastCSVHandler
from scraper.cookie_loader import load_cookies
from scraper.turbo_scraper import TurboTwitterScraper

class TwitterScraper:
    def __init__(self, num_tabs=8):  # Increased to 8 for better performance
        self.num_tabs = num_tabs
        self.proxy_manager = ProxyManager()
        self.cookies = load_cookies()
        self.csv_handler = None
        self.user_data = None
        self.lock = threading.Lock()
        self.total_scraped = 0
        self.target_reached = False
        self.turbo_mode = True  # Re-enabled with fixed turbo scraper

    def scrape(self, keyword='', hashtag='', username='', tweet_url='', tweet_urls=None, num_tweets=100, job_id=''):
        """Main scraping method with exact count targeting"""
        # Handle both single tweet_url and multiple tweet_urls
        if tweet_urls and len(tweet_urls) > 0:
            # Bulk URL mode - scrape multiple specific tweet URLs
            return self._scrape_bulk_urls(tweet_urls, job_id)
        
        search_url = self.build_url(keyword, hashtag, username, tweet_url)
        
        # Use TURBO MODE for 25+ tweets (lowered threshold)
        if self.turbo_mode and num_tweets >= 25:
            print(f"🚀 TURBO MODE: Targeting {num_tweets} tweets with async scraping")
            try:
                turbo_scraper = TurboTwitterScraper()
                result = turbo_scraper.scrape_turbo(search_url, num_tweets, job_id)
                if result:
                    return result
                else:
                    print("⚠️ Turbo mode failed, falling back to standard mode")
            except Exception as e:
                print(f"⚠️ Turbo mode error: {e}, falling back to standard mode")
        
        # ENHANCED STANDARD MODE with exact count targeting
        return self._scrape_enhanced(search_url, num_tweets, job_id)
    
    def _scrape_enhanced(self, search_url, num_tweets, job_id):
        """Enhanced standard mode for exact tweet count"""
        self.csv_handler = FastCSVHandler(job_id) if num_tweets >= 50 else CSVHandler(job_id)
        self.scraping_username = '' 
        self.job_id = job_id
        
        print(f"🚀 ENHANCED STANDARD MODE: {self.num_tabs} parallel tabs")
        print(f"🎯 Target: {num_tweets} tweets (exact count mode)")
        
        # Reset counters
        self.total_scraped = 0
        self.target_reached = False
        
        # Use aggressive parallel scraping for exact count
        with ThreadPoolExecutor(max_workers=self.num_tabs) as executor:
            futures = []
            
            for i in range(self.num_tabs):
                future = executor.submit(
                    self.scrape_tab_exact,
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
        if final_count < num_tweets * 0.85:  # If less than 85% of target
            print(f"🔄 Got {final_count}/{num_tweets} tweets, trying additional collection...")
            remaining = num_tweets - final_count
            self.target_reached = False
            
            # Quick additional scrape with fewer tabs
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for i in range(3):
                    future = executor.submit(
                        self.scrape_tab_exact,
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
    
    def _scrape_bulk_urls(self, tweet_urls, job_id):
        """Handle bulk URL scraping for specific tweet URLs"""
        self.csv_handler = CSVHandler(job_id)
        self.job_id = job_id
        
        print(f"📋 BULK URL MODE: Scraping {len(tweet_urls)} specific tweet URLs")
        
        # Reset counters
        self.total_scraped = 0
        self.target_reached = False
        
        # Use fewer tabs for URL-specific scraping (each URL is independent)
        max_workers = min(4, len(tweet_urls))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            for i, url in enumerate(tweet_urls):
                future = executor.submit(
                    self.scrape_single_url,
                    url.strip(),
                    i
                )
                futures.append(future)
            
            # Wait for completion
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"❌ URL scraping error: {e}")
        
        final_count = self.csv_handler.get_tweet_count()
        print(f"✅ Bulk URL scraping complete! Collected {final_count} tweets from {len(tweet_urls)} URLs")
        
        return self.csv_handler.get_filename() if final_count > 0 else None

    def scrape_single_url(self, tweet_url, worker_id):
        """Scrape a single specific tweet URL"""
        context = None
        page = None
        
        try:
            proxy = self.proxy_manager.get_next_proxy()
            playwright = sync_playwright().start()
            
            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                ],
                proxy=proxy if proxy else None
            )
            
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            if self.cookies:
                context.add_cookies(self.cookies)
            
            page = context.new_page()
            
            print(f"🔗 Worker {worker_id}: Scraping {tweet_url}")
            page.goto(tweet_url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(random.uniform(2, 4))
            
            # Extract the specific tweet
            tweets = self.extract_tweets_optimized(page, max_tweets=1)
            
            if tweets:
                tweet = tweets[0]  # Should only be one tweet per URL
                if self.csv_handler.add_tweet(tweet):
                    with self.lock:
                        self.total_scraped += 1
                    print(f"✅ Worker {worker_id}: Successfully scraped tweet from URL")
                else:
                    print(f"⚠️ Worker {worker_id}: Tweet already exists (duplicate)")
            else:
                print(f"❌ Worker {worker_id}: No tweet found at URL")
                
        except Exception as e:
            print(f"❌ Worker {worker_id}: Error scraping URL {tweet_url}: {e}")
            
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

    def scrape_tab_exact(self, search_url, num_tweets, tab_id):
        """Exact count scraping method"""
        context = None
        page = None
        
        try:
            proxy = self.proxy_manager.get_next_proxy()
            playwright = sync_playwright().start()
            
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
                '--disable-images',
                '--disable-plugins',
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
            
            if self.cookies:
                context.add_cookies(self.cookies)
            
            page = context.new_page()
            
            # Navigate with better error handling
            try:
                print(f"Tab {tab_id}: Navigating to {search_url}")
                response = page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
                
                if response and response.status >= 400:
                    print(f"❌ Tab {tab_id}: HTTP {response.status} - Server error")
                    return
                
                # Wait for content to load
                try:
                    # Wait for either tweets or main content
                    page.wait_for_selector('main, [data-testid="primaryColumn"], article', timeout=10000)
                    time.sleep(random.uniform(2, 3))
                except:
                    print(f"⚠️ Tab {tab_id}: Page took longer to load, continuing...")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"❌ Tab {tab_id}: Navigation failed: {e}")
                return
            
            scraped_tweets = 0
            scroll_attempts = 0
            max_scroll_attempts = 20  # Reduced from 30 to 20
            consecutive_failures = 0
            early_exit_counter = 0
            
            while scraped_tweets < num_tweets and scroll_attempts < max_scroll_attempts and not self.target_reached:
                try:
                    current_total = self.csv_handler.get_tweet_count()
                    
                    if current_total >= num_tweets:
                        print(f"🎯 Tab {tab_id}: Global target reached! ({current_total}/{num_tweets})")
                        self.target_reached = True
                        break
                    
                    tweets = self.extract_tweets_optimized(page, min(20, num_tweets - current_total))
                    
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
                    
                    if self.target_reached or self.csv_handler.get_tweet_count() >= num_tweets:
                        break
                    
                    # Early exit if no tweets found at all after multiple attempts
                    if scraped_tweets == 0 and scroll_attempts > 8:
                        early_exit_counter += 1
                        if early_exit_counter >= 3:
                            print(f"🚫 Tab {tab_id}: No tweets found after 8+ scrolls, likely blocked or wrong URL")
                            break
                    
                    if consecutive_failures >= 3:  # Reduced from 5 to 3
                        print(f"⏭️ Tab {tab_id}: No progress, trying different approach...")
                        
                        # Try to detect if page is blocked or empty
                        try:
                            page_text = page.inner_text('body')
                            if 'sign up' in page_text.lower() or 'log in' in page_text.lower() or len(page_text) < 100:
                                print(f"🚫 Tab {tab_id}: Page appears blocked or requires login, stopping")
                                break
                        except:
                            pass
                        
                        # Try refreshing the page once
                        if consecutive_failures == 3:
                            print(f"🔄 Tab {tab_id}: Refreshing page...")
                            try:
                                page.reload(wait_until='domcontentloaded', timeout=15000)
                                time.sleep(2)
                            except:
                                pass
                        
                        # Hard exit if too many failures
                        if consecutive_failures >= 6:
                            print(f"🛑 Tab {tab_id}: Too many failures, stopping this tab")
                            break
                        
                        consecutive_failures += 1
                        
                    page.evaluate('window.scrollBy(0, window.innerHeight * 2.5)')
                    time.sleep(random.uniform(0.4, 0.8))
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

    def extract_tweets_optimized(self, page, max_tweets=20):
        """Optimized tweet extraction with better data quality"""
        tweets = []
        
        try:
            # Wait a moment for content to load
            time.sleep(0.5)
            
            # Try multiple selectors for tweets
            tweet_elements = []
            selectors_to_try = [
                'article[data-testid="tweet"]',
                'div[data-testid="tweet"]', 
                'article[role="article"]',
                '[data-testid="tweetText"]'
            ]
            
            for selector in selectors_to_try:
                elements = page.query_selector_all(selector)
                if elements:
                    tweet_elements = elements[:max_tweets]
                    print(f"📍 Found {len(tweet_elements)} elements with selector: {selector}")
                    break
            
            if not tweet_elements:
                print("⚠️ No tweet elements found with any selector")
                return tweets
            
            for element in tweet_elements:
                try:
                    if element.query_selector('[data-testid="promotedIndicator"]'):
                        continue
                    
                    # Try multiple text selectors
                    text = None
                    text_selectors = [
                        '[data-testid="tweetText"]',
                        'div[lang]',  # Tweets often have lang attribute
                        'span:not([aria-hidden="true"])',  # Visible spans
                        'div[dir="auto"]'  # Auto-direction divs often contain text
                    ]
                    
                    for text_selector in text_selectors:
                        text_elem = element.query_selector(text_selector)
                        if text_elem:
                            text = text_elem.inner_text().strip()
                            if text and len(text) > 3:
                                break
                    
                    if not text:
                        continue
                    
                    if text.startswith('RT @') or 'Replying to' in text[:50]:
                        continue
                    
                    status_link = element.query_selector('a[href*="/status/"]')
                    if not status_link:
                        continue
                    
                    href = status_link.get_attribute('href')
                    if not href:
                        continue
                    
                    parts = href.split('/status/')
                    if len(parts) < 2:
                        continue
                    
                    tweet_id = parts[1].split('?')[0]
                    username = parts[0].split('/')[-1]
                    
                    # Extract engagement metrics with multiple fallbacks
                    likes = self.extract_metric(element, 'like') or '0'
                    retweets = self.extract_metric(element, 'retweet') or '0'
                    replies = self.extract_metric(element, 'reply') or '0'
                    
                    # Extract hashtags and mentions with improved regex
                    import re
                    hashtags = ', '.join(re.findall(r'#[\\w\\u00c0-\\u017f\\u0400-\\u04ff\\u4e00-\\u9fff]+', text, re.UNICODE))
                    mentions = ', '.join(re.findall(r'@[\\w\\u00c0-\\u017f\\u0400-\\u04ff\\u4e00-\\u9fff]+', text, re.UNICODE))
                    
                    # Get timestamp
                    time_elem = element.query_selector('time')
                    timestamp = time_elem.get_attribute('datetime') if time_elem else ''
                    
                    # Get profile link
                    profile_link = f"https://x.com/{username}"
                    
                    tweet = {
                        'username': username,
                        'text': text,
                        'tweet_id': tweet_id,
                        'timestamp': timestamp,
                        'likes': likes,
                        'retweets': retweets,
                        'replies': replies,
                        'hashtags': hashtags,
                        'mentions': mentions,
                        'profile_link': profile_link,
                        'tweet_link': f"https://x.com{href}"
                    }
                    
                    tweets.append(tweet)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Extract error: {e}")
        
        return tweets

    def extract_metric(self, element, metric_type):
        """Extract engagement metrics with multiple selector strategies"""
        try:
            # Multiple selector strategies for different Twitter layouts
            selectors = {
                'like': [
                    '[data-testid="like"] span span',
                    '[aria-label*="like"] span',
                    '[data-testid="like"] span',
                    'div[role="group"] div:nth-child(4) span span',
                    '[data-testid="like"]'
                ],
                'retweet': [
                    '[data-testid="retweet"] span span',
                    '[aria-label*="retweet"] span',
                    '[data-testid="retweet"] span',
                    'div[role="group"] div:nth-child(2) span span',
                    '[data-testid="retweet"]'
                ],
                'reply': [
                    '[data-testid="reply"] span span',
                    '[aria-label*="repl"] span',
                    '[data-testid="reply"] span',
                    'div[role="group"] div:nth-child(1) span span',
                    '[data-testid="reply"]'
                ]
            }
            
            for selector in selectors.get(metric_type, []):
                try:
                    elem = element.query_selector(selector)
                    if elem:
                        text = elem.inner_text().strip()
                        if text and text.isdigit():
                            return text
                        elif text:
                            # Handle K/M abbreviations
                            if 'K' in text.upper():
                                return str(int(float(text.upper().replace('K', '')) * 1000))
                            elif 'M' in text.upper():
                                return str(int(float(text.upper().replace('M', '')) * 1000000))
                except:
                    continue
            
            return '0'
        except:
            return '0'

    def build_url(self, keyword, hashtag, username, tweet_url):
        """Build search URL"""
        if tweet_url:
            return tweet_url
        
        if username:
            return f'https://x.com/{username}'
            
        if hashtag:
            encoded_hashtag = quote(f'#{hashtag}')
            return f'https://x.com/search?q={encoded_hashtag}&src=typed_query&f=live'
        
        if keyword:
            encoded_keyword = quote(keyword)
            return f'https://x.com/search?q={encoded_keyword}&src=typed_query&f=live'
        
        return 'https://x.com/home'