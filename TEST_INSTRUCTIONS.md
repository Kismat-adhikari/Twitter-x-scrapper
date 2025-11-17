# Real-Time CSV Writing - How It Works

## What Changed

The scraper now writes tweets to CSV **immediately** as they're scraped, instead of waiting until the end.

## Benefits

1. **Real-time progress** - Open the CSV file while scraping to see tweets appearing live
2. **No data loss** - If scraping crashes, all scraped tweets are already saved
3. **Thread-safe** - Multiple tabs can write simultaneously without corruption
4. **Automatic deduplication** - Duplicate tweets are skipped automatically

## How to Test

1. Start Flask:
   ```bash
   python app.py
   ```

2. Open browser: http://localhost:5000

3. Enter search (example):
   - Keyword: `AI`
   - Number of tweets: 50

4. Click "Start Scraping"

5. **While scraping**, open the CSV file in `scraped_data/` folder
   - You'll see tweets appearing one by one in real-time!
   - File format: `twitter_scrape_YYYYMMDD_HHMMSS.csv`

## Terminal Output

You'll see emojis showing progress:
- 🚀 Starting scrape
- 🎯 Target reached
- ✅ Wrote X new tweets
- ⏳ No new tweets
- 🛑 Stopping

## CSV Structure - Tweets

Each row contains:
- **tweet_id** - Unique identifier
- **tweet_url** - Direct link to tweet
- **username** - Author's handle (@username)
- **display_name** - Author's display name
- **verified** - True/False if account is verified
- **text** - Tweet content
- **timestamp** - When posted (ISO format)
- **language** - Always 'en' (English only)
- **tweet_type** - original, quote, or thread_start
- **likes** - Number of likes
- **retweets** - Number of retweets
- **replies** - Number of replies
- **engagement_rate** - (likes + retweets + replies) / followers (if available)
- **hashtags** - All #hashtags in tweet
- **mentions** - All @mentions in tweet
- **media_urls** - Image/video URLs
- **is_original** - Always True (only original tweets scraped)

## CSV Structure - User Profile (when scraping username)

Separate file: `twitter_user_YYYYMMDD_HHMMSS.csv`
- **username** - Handle
- **display_name** - Full name
- **bio** - Profile description
- **followers** - Follower count
- **following** - Following count
- **total_tweets** - Total posts
- **verified** - True/False

## Filtering Rules

The scraper now **only collects English, original tweets** and skips:
- ❌ Non-English tweets (lang != 'en')
- ❌ Replies (tweets with "Replying to @username")
- ❌ Retweets (tweets with retweet indicators)
- ❌ Manual retweets (tweets starting with "RT @")
- ❌ Promoted tweets
- ❌ Recommendations

This ensures you get **pure, original English content** only!

## Technical Details

- Uses `threading.Lock()` for thread-safe writing
- Tracks seen tweet IDs in memory to prevent duplicates
- Opens CSV in append mode for each write
- UTF-8 encoding with BOM for Excel compatibility
