import csv
import os
from datetime import datetime
import threading

class CSVHandler:
    def __init__(self, job_id=None):
        self.timestamp = job_id or datetime.now().strftime('%Y%m%d_%H%M%S')
        self.tweets_file = f'scraped_data/twitter_scrape_{self.timestamp}.csv'
        self.seen_tweet_ids = set()
        self.write_lock = threading.Lock()
        self.tweet_count = 0
        
        # Create CSV with headers
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Create CSV file with headers"""
        os.makedirs('scraped_data', exist_ok=True)
        
        with open(self.tweets_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'tweet_id', 'tweet_url', 'username', 'display_name', 'verified',
                'text', 'timestamp', 'language', 'tweet_type',
                'likes', 'retweets', 'replies', 'engagement_rate',
                'hashtags', 'mentions', 'media_urls', 'is_original'
            ])
            writer.writeheader()
        
        print(f"📝 Created CSV file: {self.tweets_file}")
    
    def append_tweet(self, tweet_data):
        """Append a single tweet to CSV (thread-safe)"""
        tweet_id = tweet_data.get('tweet_id')
        
        # Check for duplicates
        with self.write_lock:
            if tweet_id in self.seen_tweet_ids:
                return False
            
            self.seen_tweet_ids.add(tweet_id)
            
            # Append to CSV
            try:
                with open(self.tweets_file, 'a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'tweet_id', 'tweet_url', 'username', 'display_name', 'verified',
                        'text', 'timestamp', 'language', 'tweet_type',
                        'likes', 'retweets', 'replies', 'engagement_rate',
                        'hashtags', 'mentions', 'media_urls', 'is_original'
                    ])
                    writer.writerow(tweet_data)
                
                self.tweet_count += 1
                return True
            except Exception as e:
                print(f"❌ Error writing tweet to CSV: {e}")
                return False
    
    def get_filename(self):
        """Get the CSV filename"""
        return f'twitter_scrape_{self.timestamp}.csv'
    
    def get_tweet_count(self):
        """Get current number of tweets saved"""
        return self.tweet_count

    def save_user_profile(self, user_data):
        """Save user profile data to a separate CSV"""
        user_file = f'scraped_data/twitter_user_{self.timestamp}.csv'
        
        try:
            with open(user_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'username', 'display_name', 'bio', 'followers', 
                    'following', 'total_tweets', 'verified'
                ])
                writer.writeheader()
                writer.writerow(user_data)
            
            print(f"✅ User profile saved to: {user_file}")
        except Exception as e:
            print(f"❌ Error saving user profile: {e}")
