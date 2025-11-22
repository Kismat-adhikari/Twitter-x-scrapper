import csv
import os
import threading
from typing import List, Dict
from collections import deque
import time

class FastCSVHandler:
    def __init__(self, job_id=None, batch_size=50):
        self.job_id = job_id or int(time.time())
        self.tweets_file = f'scraped_data/twitter_scrape_{self.job_id}.csv'
        self.batch_size = batch_size
        self.tweet_buffer = deque()
        self.seen_tweet_ids = set()
        self.write_lock = threading.Lock()
        self.tweet_count = 0
        self.last_flush = time.time()
        
        # Create CSV with headers
        self._initialize_csv()
        
        # Start background flusher
        self._start_background_flusher()
    
    def _initialize_csv(self):
        """Create CSV file with headers"""
        os.makedirs('scraped_data', exist_ok=True)
        
        fieldnames = [
            'tweet_id', 'tweet_url', 'username', 'display_name', 'verified',
            'text', 'timestamp', 'language', 'tweet_type',
            'likes', 'retweets', 'replies', 'quotes', 'bookmarks', 'views', 'engagement_rate',
            'hashtags', 'mentions', 'media_urls', 'is_original',
            'tweet_link', 'profile_link'
        ]
        
        with open(self.tweets_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    
    def add_tweet(self, tweet_data: Dict) -> bool:
        """Alias for append_tweet for compatibility"""
        return self.append_tweet(tweet_data)

    def append_tweet(self, tweet_data: Dict) -> bool:
        """Add tweet to buffer (faster than immediate write)"""
        tweet_id = tweet_data.get('tweet_id')
        
        with self.write_lock:
            if tweet_id in self.seen_tweet_ids:
                return False
            
            self.seen_tweet_ids.add(tweet_id)
            self.tweet_buffer.append(tweet_data)
            self.tweet_count += 1
            
            # Force flush if buffer is full or it's been too long
            if (len(self.tweet_buffer) >= self.batch_size or 
                time.time() - self.last_flush > 1.0):
                self._flush_buffer()
            
            return True
    
    def _flush_buffer(self):
        """Write buffered tweets to CSV"""
        if not self.tweet_buffer:
            return
        
        try:
            fieldnames = [
                'tweet_id', 'tweet_url', 'username', 'display_name', 'verified',
                'text', 'timestamp', 'language', 'tweet_type',
                'likes', 'retweets', 'replies', 'quotes', 'bookmarks', 'views', 'engagement_rate',
                'hashtags', 'mentions', 'media_urls', 'is_original',
                'tweet_link', 'profile_link'
            ]
            
            with open(self.tweets_file, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                
                while self.tweet_buffer:
                    tweet = self.tweet_buffer.popleft()
                    writer.writerow(tweet)
            
            self.last_flush = time.time()
            
        except Exception as e:
            print(f"❌ Error flushing to CSV: {e}")
    
    def _start_background_flusher(self):
        """Start background thread to flush buffer periodically"""
        def flush_worker():
            while True:
                time.sleep(1)  # Check every second
                with self.write_lock:
                    if self.tweet_buffer and time.time() - self.last_flush > 3:
                        self._flush_buffer()
        
        thread = threading.Thread(target=flush_worker, daemon=True)
        thread.start()
    
    def force_flush(self):
        """Force immediate flush of all buffered data"""
        with self.write_lock:
            self._flush_buffer()
    
    def get_filename(self):
        return f'twitter_scrape_{self.job_id}.csv'
    
    def get_tweet_count(self):
        return self.tweet_count