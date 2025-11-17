# Twitter Scraper - Complete Feature List

## 🎯 Scraping Modes

1. **Keyword Search** - Search for any keyword (e.g., "AI", "Python")
2. **Hashtag Search** - Search by hashtag (e.g., "#machinelearning")
3. **Username Profile** - Scrape tweets from a specific user + their profile data
4. **Tweet URL** - Scrape a specific tweet by URL

## 🔍 Filtering Rules

### ✅ What Gets Scraped:
- **English tweets only** (lang="en")
- **Original tweets** - User's own content
- **Quote tweets** - Tweets with quoted content
- **Thread starters** - First tweet in a thread
- **Tweets with media** - Photos, videos, links

### ❌ What Gets Skipped:
- Non-English tweets
- Replies (tweets with "Replying to @username")
- Retweets (both automatic and manual "RT @")
- Promoted tweets / Ads
- Recommendations

## 📊 Data Fields - Per Tweet (16 fields)

| Field | Description | Example |
|-------|-------------|---------|
| tweet_id | Unique identifier | 1234567890 |
| tweet_url | Direct link | https://x.com/user/status/123 |
| username | Author's handle | elonmusk |
| display_name | Author's full name | Elon Musk |
| verified | Verified account | True/False |
| text | Tweet content | "Just launched..." |
| timestamp | When posted | 2025-11-17T14:30:00.000Z |
| language | Language code | en |
| tweet_type | Type of tweet | original/quote/thread_start |
| likes | Like count | 1500 |
| retweets | Retweet count | 250 |
| replies | Reply count | 89 |
| engagement_rate | Engagement metric | (calculated if possible) |
| hashtags | All hashtags | #AI, #Python |
| mentions | All mentions | @openai, @anthropic |
| media_urls | Image/video URLs | https://pbs.twimg.com/... |
| is_original | Original tweet flag | True |

## 👤 Data Fields - Per User Profile (7 fields)

When scraping a username, a separate CSV is created with:

| Field | Description | Example |
|-------|-------------|---------|
| username | Handle | elonmusk |
| display_name | Full name | Elon Musk |
| bio | Profile description | CEO of Tesla, SpaceX... |
| followers | Follower count | 150M |
| following | Following count | 500 |
| total_tweets | Total posts | 25K |
| verified | Verified status | True |

## ⚡ Performance Features

1. **Parallel Scraping** - 4 browser tabs running simultaneously
2. **Proxy Rotation** - Each tab uses a different proxy from `proxies.txt`
3. **Real-time CSV Writing** - Tweets saved immediately as scraped
4. **Thread-safe** - Multiple tabs write safely without corruption
5. **Automatic Deduplication** - Duplicate tweets skipped automatically
6. **Natural Scrolling** - Mimics human behavior
7. **Smart Stopping** - Stops when target reached or no new tweets

## 📁 Output Files

### Tweets CSV
- Location: `scraped_data/twitter_scrape_YYYYMMDD_HHMMSS.csv`
- Format: UTF-8 with BOM (Excel compatible)
- Updates: Real-time (each tweet appended immediately)

### User Profile CSV (optional)
- Location: `scraped_data/twitter_user_YYYYMMDD_HHMMSS.csv`
- Created when: Scraping a username
- Contains: Full profile data

## 🔧 Technical Stack

- **Playwright** - Browser automation
- **Flask** - Web framework
- **Threading** - Parallel execution
- **CSV** - Data storage
- **Regex** - Hashtag/mention extraction

## 🚀 Usage Examples

### Example 1: Keyword Search
```
Keyword: AI
Hashtag: (empty)
Username: (empty)
Tweets: 50
```
Result: 50 English tweets about AI

### Example 2: Hashtag Search
```
Keyword: (empty)
Hashtag: python
Username: (empty)
Tweets: 100
```
Result: 100 English tweets with #python

### Example 3: User Profile
```
Keyword: (empty)
Hashtag: (empty)
Username: elonmusk
Tweets: 20
```
Result: 
- 20 tweets from @elonmusk
- User profile CSV with bio, followers, etc.

## 📈 Data Quality

- **Accuracy**: Only verified, original content
- **Completeness**: All 16 data fields per tweet
- **Freshness**: Real-time scraping
- **Language**: 100% English
- **Deduplication**: No duplicate tweets

## 🎨 Terminal Output

Real-time progress with emojis:
- 🚀 Starting scrape
- 🎯 Target reached
- ✅ Wrote tweets to CSV
- 🌐 Skipping non-English
- 💬 Skipping reply
- 🔄 Skipping retweet
- 🚫 Skipping promoted
- ⏳ No new tweets
- 🛑 Stopping
- 📊 User profile scraped

## 🔮 Future Enhancements (Optional)

- Sentiment analysis per tweet
- Topic classification
- Media file downloads
- Export to JSON/Excel
- Scheduled scraping
- Email notifications
- Dashboard UI
