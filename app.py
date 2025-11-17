from flask import Flask, render_template, request, jsonify
import threading
import os
from datetime import datetime
from scraper.playwright_scraper import TwitterScraper

app = Flask(__name__)

# Ensure scraped_data folder exists
os.makedirs('scraped_data', exist_ok=True)

# Store active scraping jobs
active_jobs = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    
    keyword = data.get('keyword', '').strip()
    hashtag = data.get('hashtag', '').strip()
    username = data.get('username', '').strip()
    tweet_url = data.get('tweet_url', '').strip()
    num_tweets = int(data.get('num_tweets', 50))
    
    # Validate input
    if not any([keyword, hashtag, username, tweet_url]):
        return jsonify({'error': 'Please provide at least one search parameter'}), 400
    
    # Generate job ID
    job_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Start scraping in background thread
    thread = threading.Thread(
        target=run_scraper,
        args=(job_id, keyword, hashtag, username, tweet_url, num_tweets)
    )
    thread.daemon = True
    thread.start()
    
    active_jobs[job_id] = {'status': 'running', 'filename': None}
    
    return jsonify({
        'message': 'Scrape started. Data will be saved as a CSV file on the server.',
        'job_id': job_id
    })

def run_scraper(job_id, keyword, hashtag, username, tweet_url, num_tweets):
    try:
        print(f"🚀 Starting scraper job {job_id}")
        
        # Initialize job with filename immediately
        filename = f'twitter_scrape_{job_id}.csv'
        active_jobs[job_id] = {
            'status': 'running',
            'filename': filename,
            'progress': 0,
            'target': num_tweets
        }
        
        scraper = TwitterScraper()
        result_filename = scraper.scrape(
            keyword=keyword,
            hashtag=hashtag,
            username=username,
            tweet_url=tweet_url,
            num_tweets=num_tweets,
            job_id=job_id
        )
        
        if result_filename:
            active_jobs[job_id] = {
                'status': 'completed',
                'filename': result_filename,
                'progress': 100,
                'target': num_tweets
            }
            print(f"✅ Job {job_id} completed: {result_filename}")
        else:
            active_jobs[job_id] = {
                'status': 'failed',
                'error': 'No tweets collected',
                'progress': 0,
                'target': num_tweets
            }
            print(f"❌ Job {job_id} failed: No tweets collected")
            
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        active_jobs[job_id] = {
            'status': 'failed',
            'error': error_msg,
            'progress': 0,
            'target': num_tweets
        }
        print(f"❌ Scraping error in job {job_id}: {error_msg}")

@app.route('/status/<job_id>')
def get_status(job_id):
    if job_id in active_jobs:
        return jsonify(active_jobs[job_id])
    return jsonify({'error': 'Job not found'}), 404

@app.route('/tweets/<job_id>')
def get_tweets(job_id):
    """Get scraped tweets for a job in real-time"""
    if job_id in active_jobs:
        job_data = active_jobs[job_id]
        
        # Read tweets from CSV if file exists
        if job_data.get('filename'):
            import csv
            tweets = []
            csv_path = f'scraped_data/{job_data["filename"]}'
            
            try:
                with open(csv_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    tweets = list(reader)
                
                return jsonify({
                    'tweets': tweets,
                    'count': len(tweets),
                    'status': job_data.get('status', 'running')
                })
            except FileNotFoundError:
                return jsonify({'tweets': [], 'count': 0, 'status': 'running'})
        
        return jsonify({'tweets': [], 'count': 0, 'status': 'running'})
    
    return jsonify({'error': 'Job not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
