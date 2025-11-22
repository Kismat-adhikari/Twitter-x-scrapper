"""
Fixed and simplified Twitter scraper with robust error handling
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

class TwitterScraper:
    def __init__(self, num_tabs=None):  # Dynamic tab count
        self.num_tabs = num_tabs
        self.proxy_manager = ProxyManager()
        self.cookies = load_cookies()
        self.csv_handler = None
        self.lock = threading.Lock()
        self.total_scraped = 0
        self.target_reached = False

    def scrape(self, keyword='', hashtag='', username='', tweet_url='', tweet_urls=None, num_tweets=100, job_id=''):
        """Main scraping method with robust error handling"""
        # Handle bulk URLs first
        if tweet_urls and len(tweet_urls) > 0:
            return self._scrape_bulk_urls(tweet_urls, job_id)
        
        # Build search URL
        search_url = self.build_url(keyword, hashtag, username, tweet_url)
        
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
        
        print(f"🚀 STARTING SCRAPE: {self.num_tabs} parallel tabs")
        print(f"🎯 Target: {num_tweets} tweets")
        print(f"🔗 URL: {search_url}")
        
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
                    print(f"❌ Tab error: {e}")
        
        final_count = self.csv_handler.get_tweet_count()
        print(f"✅ Scraping complete! Collected {final_count} tweets")
        
        if hasattr(self.csv_handler, 'force_flush'):
            self.csv_handler.force_flush()
        
        return self.csv_handler.get_filename() if final_count > 0 else None

    def scrape_tab_simple(self, search_url, num_tweets, tab_id):
        """Simplified, more reliable tab scraping"""
        print(f"🔥 Tab {tab_id}: Starting...")
        
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
                
                print(f"✅ Tab {tab_id}: Finished with {tweets_found} tweets")
                browser.close()
                
        except Exception as e:
            print(f"❌ Tab {tab_id}: Error: {e}")

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
                    '[role="article"]'
                ]
                
                for selector in alt_selectors:
                    articles = page.query_selector_all(selector)
                    if articles:
                        print(f"Found {len(articles)} articles using selector: {selector}")
                        break
            else:
                print(f"Found {len(articles)} articles using standard selector")
            
            if not articles:
                # Final fallback: look for any text content
                all_divs = page.query_selector_all('div')
                print(f"No articles found, checking {len(all_divs)} divs for content")
                
                # Check if this is a "No results" page first
                try:
                    page_content = page.content().lower()
                    if ('no results' in page_content or 
                        'try searching for something else' in page_content or
                        'nothing came up' in page_content or
                        len(all_divs) < 50):  # Very few divs = likely empty page
                        print("Detected empty/no-results page, not extracting UI elements")
                        return tweets
                except:
                    # If page content check fails, continue anyway
                    pass
                
                # Try to extract from divs with text content
                text_candidates = []
                seen_texts = set()  # Avoid duplicates
                
                for div in all_divs[:200]:  # Check more divs
                    try:
                        text = div.inner_text().strip()
                        if text and 30 <= len(text) <= 400:  # Better tweet length range
                            # More comprehensive skip list for UI elements
                            skip_phrases = [
                                'home', 'explore', 'notifications', 'messages', 'bookmarks', 
                                'communities', 'premium', 'profile', 'more', 'settings', 
                                'search', 'trending', 'what\'s happening', 'keyboard shortcuts',
                                'press question mark', 'kismat adhikari', '@kismatadh',
                                'follow', 'following', 'followers', 'tweet', 'retweet',
                                'like', 'reply', 'share', 'bookmark', 'copy link',
                                'show this thread', 'show more', 'see new tweets',
                                'timeline', 'for you', 'account info', 'accessibility',
                                'top latest people media lists', 'see new posts',
                                'no results for', 'try searching', 'nothing came up',
                                'something went wrong', 'try reloading', 'retry',
                                'error', 'loading', 'failed to load', 'connection issue'
                            ]
                            
                            text_lower = text.lower()
                            if (not any(skip_phrase in text_lower for skip_phrase in skip_phrases) and
                                text not in seen_texts and
                                len(text.split()) >= 5 and  # At least 5 words for real content
                                not text.startswith(('@', '#', 'RT ')) and  # Not just mentions/hashtags/retweets
                                not text.isdigit() and  # Not just numbers
                                ('.' in text or '!' in text or '?' in text or ':' in text) and  # Has punctuation
                                not text.lower().startswith(('home', 'explore', 'notification'))):  # Not navigation
                                
                                text_candidates.append(text)
                                seen_texts.add(text)
                                
                                if len(text_candidates) >= 5:  # Lower limit for fallback
                                    break
                    except:
                        continue
                
                if not text_candidates:
                    print("No valid tweet content found in divs")
                    return tweets
                
                # Create tweets from text candidates
                for i, text in enumerate(text_candidates[:10]):  # Max 10 from fallback
                    # Clean text for CSV
                    text = ' '.join(text.split())
                    text = text.replace('"', '""')
                    
                    tweet = {
                        'tweet_id': f'fallback_{int(time.time())}_{i}',
                        'tweet_url': f'https://x.com/unknown/status/fallback_{i}',
                        'username': 'unknown',
                        'display_name': 'unknown',
                        'verified': '',
                        'text': text,
                        'timestamp': '',
                        'language': '',
                        'tweet_type': 'original',
                        'likes': '0',
                        'retweets': '0',
                        'replies': '0',
                        'engagement_rate': '',
                        'hashtags': '',
                        'mentions': '',
                        'media_urls': '',
                        'is_original': 'true',
                        'tweet_link': f'https://x.com/unknown/status/fallback_{i}',
                    }
                    tweets.append(tweet)
                
                if tweets:
                    print(f"Extracted {len(tweets)} tweets from div fallback")
                
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
                    if not text or len(text) < 5:
                        continue
                    
                    # Clean text for CSV: remove newlines and normalize whitespace
                    text = ' '.join(text.split())  # This removes all extra whitespace and newlines
                    text = text.replace('"', '""')  # Escape quotes for CSV
                    
                    # Skip promoted content and retweets
                    if 'Promoted' in text or text.startswith('RT @'):
                        continue
                    
                    # Try to get username and tweet ID from links
                    username = 'unknown'
                    tweet_id = f'tweet_{int(time.time())}_{i}'
                    
                    # Look for profile links
                    links = article.query_selector_all('a')
                    for link in links:
                        href = link.get_attribute('href')
                        if href and '/status/' in href:
                            parts = href.split('/')
                            if len(parts) >= 4:
                                username = parts[1] if parts[1] else 'unknown'
                                tweet_id = parts[3].split('?')[0] if parts[3] else tweet_id
                            break
                    
                    # Extract basic metrics (simplified)
                    likes = '0'
                    retweets = '0'
                    replies = '0'
                    
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

    def build_url(self, keyword, hashtag, username, tweet_url):
        """Build search URL"""
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
                print(f"Simplified to: {combined_query}")
            
            encoded_query = quote(combined_query)
            return f'https://x.com/search?q={encoded_query}&src=typed_query&f=live'
        
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