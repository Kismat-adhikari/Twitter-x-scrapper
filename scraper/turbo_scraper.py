import asyncio
import aiofiles
import csv
from playwright.async_api import async_playwright
from concurrent.futures import ThreadPoolExecutor
import time
from typing import List, Dict
import threading
from scraper.fast_csv_handler import FastCSVHandler
import random
import re

class AsyncTwitterScraper:
    def __init__(self, num_workers=8):  # Reduced for stability
        self.num_workers = num_workers
        self.scraped_count = 0
        self.target_reached = False
        self.lock = asyncio.Lock()
        self.csv_handler = None
        self.job_id = None

    async def scrape_fast(self, search_url: str, target_tweets: int, job_id: str):
        """Ultra-fast async scraping with browser reuse"""
        self.job_id = job_id
        self.csv_handler = FastCSVHandler(job_id)
        
        print(f"🚀 TURBO MODE: {self.num_workers} async workers targeting {target_tweets} tweets")
        
        async with async_playwright() as p:
            # Create browser pool with optimized settings
            browsers = []
            for i in range(self.num_workers):
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-gpu',
                        '--disable-images',
                        '--disable-plugins',
                        '--disable-extensions',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--memory-pressure-off',
                        '--max_old_space_size=4096',
                        '--aggressive-cache-discard'
                    ]
                )
                browsers.append(browser)
            
            try:
                # Create tasks for parallel scraping
                tasks = []
                for i, browser in enumerate(browsers):
                    task = asyncio.create_task(
                        self._scrape_worker(browser, search_url, target_tweets, i)
                    )
                    tasks.append(task)
                
                # Wait for all workers to complete with timeout
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=120  # 2 minutes max
                    )
                except asyncio.TimeoutError:
                    print("⏰ Turbo scraping timed out")
                    for task in tasks:
                        if not task.done():
                            task.cancel()
                
            finally:
                # Cleanup
                for browser in browsers:
                    await browser.close()
        
        final_count = self.csv_handler.get_tweet_count()
        print(f"✅ TURBO SCRAPING COMPLETE: {final_count} tweets")
        return self.csv_handler.get_filename() if final_count > 0 else None

    async def _scrape_worker(self, browser, search_url: str, target_tweets: int, worker_id: int):
        """Individual async worker - optimized for exact count"""
        context = await browser.new_context()
        
        # Add cookies if available
        try:
            from scraper.cookie_loader import load_cookies
            cookies = load_cookies()
            if cookies:
                await context.add_cookies(cookies)
        except Exception as e:
            print(f"Worker {worker_id}: Cookie error: {e}")
        
        page = await context.new_page()
        
        try:
            print(f"Worker {worker_id}: Navigating to {search_url}")
            await page.goto(search_url, timeout=30000)
            
            # Wait for page to load and tweets to appear
            try:
                await page.wait_for_selector('article[data-testid="tweet"]', timeout=8000)
                print(f"Worker {worker_id}: Found tweets on page")
            except:
                print(f"Worker {worker_id}: No tweets found, continuing anyway")
                await asyncio.sleep(1)
            
            # Close any popups quickly
            try:
                close_btn = await page.query_selector('[aria-label="Close"]')
                if close_btn:
                    await close_btn.click()
                    await asyncio.sleep(0.2)
            except:
                pass
            
            scroll_count = 0
            max_scrolls = 25
            no_new_tweets = 0
            
            while scroll_count < max_scrolls and not self.target_reached:
                # Check if we need more tweets
                current_count = self.csv_handler.get_tweet_count()
                if current_count >= target_tweets:
                    print(f"Worker {worker_id}: Target reached globally ({current_count}/{target_tweets})")
                    self.target_reached = True
                    break
                
                # Extract tweets async
                new_tweets = await self._extract_tweets_async(page, worker_id)
                
                tweets_saved = 0
                if new_tweets:
                    for tweet in new_tweets:
                        current_count = self.csv_handler.get_tweet_count()
                        if current_count >= target_tweets:
                            self.target_reached = True
                            break
                        
                        # Use synchronous append since FastCSVHandler is sync
                        if self.csv_handler.append_tweet(tweet):
                            tweets_saved += 1
                            
                            async with self.lock:
                                self.scraped_count += 1

                if tweets_saved > 0:
                    current_count = self.csv_handler.get_tweet_count()
                    print(f"Worker {worker_id}: +{tweets_saved} tweets (Total: {current_count}/{target_tweets})")
                    no_new_tweets = 0
                else:
                    no_new_tweets += 1
                    if no_new_tweets >= 3:  # Reduced from 4
                        print(f"Worker {worker_id}: No new tweets after 3 attempts, checking page status")
                        
                        # Check if page is blocked
                        try:
                            page_text = await page.inner_text('body')
                            if 'sign up' in page_text.lower() or 'log in' in page_text.lower() or len(page_text) < 100:
                                print(f"Worker {worker_id}: Page appears blocked, stopping")
                                break
                        except:
                            pass
                        
                        if no_new_tweets >= 5:  # Hard exit
                            print(f"Worker {worker_id}: Too many failed attempts, stopping")
                            break

                if self.target_reached:
                    break
                
                # Scroll down with faster timing
                await page.evaluate('window.scrollBy(0, window.innerHeight * 2.5)')
                await asyncio.sleep(0.4)
                scroll_count += 1
            
            print(f"Worker {worker_id}: Completed after {scroll_count} scrolls")
            
        except Exception as e:
            print(f"Worker {worker_id}: Error: {e}")
        finally:
            await context.close()

    async def _extract_tweets_async(self, page, worker_id: int) -> List[Dict]:
        """Fast async tweet extraction with proper error handling"""
        tweets = []
        
        try:
            # Get all tweet elements at once
            elements = await page.query_selector_all('article[data-testid="tweet"]')
            
            if not elements:
                return tweets
            
            for i, element in enumerate(elements[:15]):  # Limit to 15 for speed
                try:
                    # Skip promoted tweets
                    promoted = await element.query_selector('[data-testid="promotedIndicator"]')
                    if promoted:
                        continue
                    
                    # Get tweet text
                    text_elem = await element.query_selector('[data-testid="tweetText"]')
                    if not text_elem:
                        continue
                    
                    text = await text_elem.inner_text()
                    if not text or len(text.strip()) < 3:
                        continue
                    
                    text = text.strip()
                    
                    # Skip retweets and replies
                    if text.startswith('RT @') or 'Replying to' in text[:50]:
                        continue
                    
                    # Get status link
                    status_link = await element.query_selector('a[href*="/status/"]')
                    if not status_link:
                        continue
                    
                    href = await status_link.get_attribute('href')
                    if not href:
                        continue
                    
                    # Extract tweet ID and username
                    parts = href.split('/status/')
                    if len(parts) < 2:
                        continue
                    
                    tweet_id = parts[1].split('?')[0]
                    username = parts[0].split('/')[-1]
                    
                    # Extract engagement metrics
                    likes = await self._extract_metric_async(element, 'like')
                    retweets = await self._extract_metric_async(element, 'retweet')
                    replies = await self._extract_metric_async(element, 'reply')
                    
                    # Extract hashtags and mentions
                    hashtags = self._extract_hashtags(text)
                    mentions = self._extract_mentions(text)
                    
                    # Get timestamp
                    time_elem = await element.query_selector('time')
                    timestamp = await time_elem.get_attribute('datetime') if time_elem else ''
                    
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
                        'profile_link': f"https://x.com/{username}",
                        'tweet_link': f"https://x.com{href}"
                    }
                    
                    tweets.append(tweet)
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"Worker {worker_id} extraction error: {e}")
        
        return tweets
    
    async def _extract_metric_async(self, element, metric_type):
        """Extract engagement metrics asynchronously"""
        try:
            selectors = {
                'like': [
                    '[data-testid="like"] span span',
                    '[aria-label*="like"] span',
                    'div[role="group"] div:nth-child(4) span span'
                ],
                'retweet': [
                    '[data-testid="retweet"] span span',
                    '[aria-label*="retweet"] span',
                    'div[role="group"] div:nth-child(2) span span'
                ],
                'reply': [
                    '[data-testid="reply"] span span',
                    '[aria-label*="repl"] span',
                    'div[role="group"] div:nth-child(1) span span'
                ]
            }
            
            for selector in selectors.get(metric_type, []):
                try:
                    elem = await element.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        text = text.strip()
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
    
    def _extract_hashtags(self, text):
        """Extract hashtags from tweet text"""
        hashtags = re.findall(r'#[\w\u00c0-\u017f\u0400-\u04ff\u4e00-\u9fff]+', text, re.UNICODE)
        return ', '.join(hashtags) if hashtags else ''
    
    def _extract_mentions(self, text):
        """Extract mentions from tweet text"""
        mentions = re.findall(r'@[\w\u00c0-\u017f\u0400-\u04ff\u4e00-\u9fff]+', text, re.UNICODE)
        return ', '.join(mentions) if mentions else ''

    def _update_progress(self, current, total):
        """Update progress (placeholder for compatibility)"""
        pass

# Sync wrapper for compatibility with existing code
class TurboTwitterScraper:
    def __init__(self):
        self.async_scraper = AsyncTwitterScraper(num_workers=8)
    
    def scrape_turbo(self, search_url: str, target_tweets: int, job_id: str):
        """Sync wrapper for async scraping"""
        import asyncio
        
        try:
            # Run async scraper
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.async_scraper.scrape_fast(search_url, target_tweets, job_id)
            )
            loop.close()
            return result
        except Exception as e:
            print(f"Turbo scraper error: {e}")
            return None