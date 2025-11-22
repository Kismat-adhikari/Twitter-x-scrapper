# 🐦 Twitter Scraper - Complete Architecture Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [Entry Points](#entry-points)
3. [Core Components](#core-components)
4. [Scraping Flow](#scraping-flow)
5. [Data Extraction](#data-extraction)
6. [CSV Storage](#csv-storage)
7. [Key Features](#key-features)

---

## 🎯 Overview

This is a **terminal-based Twitter scraper** that uses Playwright to scrape tweets without the Twitter API. It supports parallel scraping, real-time CSV writing, and advanced filtering.

### Architecture Diagram
```
main.py (Terminal UI)
    ↓
TwitterScraper (scraper/playwright_scraper.py)
    ↓
4-8 Parallel Browser Tabs
    ↓
API Interception + DOM Scraping
    ↓
CSVHandler / FastCSVHandler
    ↓
scraped_data/twitter_scrape_TIMESTAMP.csv
```

---

## 🚀 Entry Points

### 1. Terminal Interface (main.py)
**Primary way to use the scraper**

```bash
python main.py
```

**What it does:**
1. Prompts user for search parameters:
   - Keyword (e.g., "AI technology")
   - Hashtag (e.g., "python")
   - Username (e.g., "@elonmusk")
   - Number of tweets (10-500)
   - Search mode (TOP/LIVE/PEOPLE)

2. Displays search configuration
3. Confirms before starting
4. Runs scraper
5. Shows results and preview

**Example Session:**
```
Enter keyword(s): AI
Enter hashtag: 
Enter username: 
Select mode (1/2/3): 1
Enter number of tweets: 100
Start scraping? (y/n): y
→ Scrapes 100 tweets about "AI"
```

### 2. Test Scripts
- `test_100_tweets.py` - Test 100 tweet scraping
- `test_speed.py` - Performance testing
- Other test files for specific features

---

## 🔧 Core Components

### 1. TwitterScraper (scraper/playwright_scraper.py)

**Main scraping engine**

```python
class TwitterScraper:
    def __init__(self, num_tabs=None):
        self.num_tabs = num_tabs  # Auto-calculated if None
        self.proxy_manager = ProxyManager()
        self.cookies = load_cookies()
        self.csv_handler = None
        self.total_scraped = 0
        self.target_reached = False
```

**Key Methods:**

#### `scrape(keyword, hashtag, username, num_tweets, search_mode)`
- Main entry point
- Builds search URL
- Initializes CSV handler
- Spawns parallel tabs
- Returns filename when done

#### `scrape_tab_simple(search_url, num_tweets, tab_id)`
- Runs in each parallel tab
- Opens browser with Playwright
- Intercepts API responses
- Scrolls to load more tweets
- Extracts tweets
- Writes to CSV immediately

#### `_intercept_api_response(response, tab_id)`
- Intercepts Twitter's GraphQL API
- Extracts real engagement data
- Gets follower counts, verified status
- More reliable than DOM scraping

#### `_process_api_tweet(tweet_data, tab_id, entry)`
- Processes intercepted API data
- Extracts all tweet fields
- Calculates engagement rate
- Filters by engagement threshold
- Writes to CSV

### 2. CSVHandler (scraper/csv_handler.py)

**Standard CSV writer for <50 tweets**

```python
class CSVHandler:
    def __init__(self, job_id):
        self.tweets_file = f'scraped_data/twitter_scrape_{job_id}.csv'
        self.seen_tweet_ids = set()
        self.write_lock = threading.Lock()
```

**Features:**
- Thread-safe writing
- Duplicate detection
- Immediate write (no buffering)
- 28 columns of data

### 3. FastCSVHandler (scraper/fast_csv_handler.py)

**Optimized CSV writer for ≥50 tweets**

**Improvements over CSVHandler:**
- Buffered writing (writes in batches)
- Faster for large datasets
- Auto-flushes every 10 tweets
- Force flush at end

### 4. ProxyManager (scraper/proxy_manager.py)

**Manages proxy rotation**

```python
class ProxyManager:
    def load_proxies(self, proxy_file='proxies.txt')
    def get_proxy(self) → dict
    def mark_failed(self, proxy_dict)
```

**Features:**
- Round-robin rotation
- Failure tracking
- Auto-retry failed proxies
- Format: `ip:port:username:password`

### 5. Cookie Loader (scraper/cookie_loader.py)

**Loads Twitter authentication cookies**

```python
def load_cookies(cookie_file='x.com_cookies.txt')
```

**Features:**
- Parses Netscape format
- Adds cookies to browser context
- Enables authenticated scraping

---

## 🔄 Scraping Flow

### Step-by-Step Process

```
1. USER INPUT
   ↓
   main.py prompts for:
   - keyword, hashtag, username
   - number of tweets
   - search mode
   
2. INITIALIZATION
   ↓
   TwitterScraper.scrape() called
   ↓
   - Build search URL
   - Initialize CSV handler
   - Calculate optimal tab count
   
3. PARALLEL SCRAPING
   ↓
   Spawn 4-8 browser tabs
   ↓
   Each tab:
   - Opens browser with Playwright
   - Loads cookies
   - Uses proxy (if available)
   - Navigates to search URL
   
4. API INTERCEPTION
   ↓
   Browser intercepts Twitter API calls
   ↓
   - SearchTimeline API
   - TweetDetail API
   - UserTweets API
   ↓
   Extract JSON data
   
5. DATA EXTRACTION
   ↓
   For each tweet:
   - Parse API response
   - Extract 28 fields
   - Calculate engagement rate
   - Filter by engagement threshold
   
6. CSV WRITING
   ↓
   Thread-safe write:
   - Check for duplicates
   - Append to CSV immediately
   - Increment counter
   
7. SCROLLING
   ↓
   Scroll page to load more tweets
   ↓
   - Scroll 6-8x viewport height
   - Wait 0.3-1.5 seconds
   - Repeat until target reached
   
8. STOPPING CONDITIONS
   ↓
   Stop when:
   - Target tweets reached (100/100)
   - No new tweets for 12 attempts
   - Max scrolls reached (80-150)
   
9. COMPLETION
   ↓
   - Close all browsers
   - Flush CSV buffer
   - Return filename
   - Display results
```

---

## 📊 Data Extraction

### Two Methods

#### 1. API Interception (Primary)
**More reliable, gets real data**

```python
def _intercept_api_response(response, tab_id):
    # Intercept Twitter's GraphQL API
    if 'SearchTimeline' in url:
        data = response.json()
        # Extract from JSON
```

**Advantages:**
- Real engagement numbers
- Follower counts
- Verified status
- More fields available

#### 2. DOM Scraping (Fallback)
**Used when API fails**

```python
def extract_tweets_simple(page):
    # Find tweet elements
    articles = page.query_selector_all('article')
    # Parse HTML
```

**Advantages:**
- Works when API blocked
- Simpler logic
- No JSON parsing

### Data Fields Extracted (28 total)

**Tweet Data:**
- tweet_id, tweet_url, tweet_link
- text, timestamp, language
- tweet_type (original/quote/thread)

**Author Data:**
- username, display_name, verified
- profile_link, profile_bio
- profile_location, profile_website, profile_email
- followers_count, following_count

**Engagement Data:**
- likes, retweets, replies
- quotes, bookmarks, views
- engagement_rate (calculated)

**Content Data:**
- hashtags (comma-separated)
- mentions (comma-separated)
- media_urls (comma-separated)
- is_original (True/False)

---

## 💾 CSV Storage

### File Structure

**Location:** `scraped_data/twitter_scrape_YYYYMMDD_HHMMSS.csv`

**Format:** UTF-8 with BOM (Excel compatible)

**Headers:**
```csv
tweet_id,tweet_url,username,display_name,verified,text,timestamp,language,tweet_type,likes,retweets,replies,quotes,bookmarks,views,engagement_rate,hashtags,mentions,media_urls,is_original,tweet_link,profile_link,profile_bio,profile_location,profile_website,profile_email,followers_count,following_count
```

**Example Row:**
```csv
"1234567890","https://x.com/user/status/1234567890","elonmusk","Elon Musk","True","Just launched Starship!","2025-11-22T12:00:00.000Z","en","original","50000","10000","2000","500","1000","1000000","0.0063","#SpaceX,#Starship","@NASA,@SpaceX","https://pbs.twimg.com/media/...","True","https://x.com/elonmusk/status/1234567890","https://x.com/elonmusk","CEO of Tesla, SpaceX","Palo Alto, CA","spacex.com","","150000000","500"
```

### Writing Strategy

**Standard Mode (<50 tweets):**
- Write immediately after each tweet
- No buffering
- Slower but safer

**Turbo Mode (≥50 tweets):**
- Buffer 10 tweets
- Write in batches
- 3-5x faster
- Auto-flush every 10 tweets

---

## ⚡ Key Features

### 1. Parallel Scraping
- 4-8 tabs run simultaneously
- Each tab uses different proxy
- Shared CSV handler (thread-safe)
- Stops when target reached

### 2. Smart Persistence
- Tries 12 times without new content (for 100 tweets)
- Tries 15 times for 200+ tweets
- Adjusts based on progress
- Prevents premature stopping

### 3. Engagement Filtering
**Search Modes:**
- **TOP:** Popular tweets (min 10 likes)
- **LIVE:** Latest tweets (no filter)
- **PEOPLE:** From verified accounts

**Engagement Rate:**
```python
engagement_rate = (likes + retweets + replies) / followers
```

### 4. Duplicate Prevention
- Tracks seen tweet IDs in memory
- Thread-safe set operations
- Skips duplicates automatically

### 5. Error Handling
- Retries on failure
- Proxy rotation on error
- Graceful degradation
- Detailed logging

### 6. Cookie Authentication
- Loads from `x.com_cookies.txt`
- Enables authenticated scraping
- Access to more content
- Better rate limits

---

## 🎯 Usage Examples

### Example 1: Simple Keyword Search
```bash
python main.py
# Enter keyword: AI
# Enter hashtag: 
# Enter username: 
# Select mode: 1 (TOP)
# Enter number: 100
# → Scrapes 100 popular AI tweets
```

### Example 2: Hashtag Search
```bash
python main.py
# Enter keyword: 
# Enter hashtag: python
# Enter username: 
# Select mode: 2 (LIVE)
# Enter number: 50
# → Scrapes 50 latest #python tweets
```

### Example 3: User Timeline
```bash
python main.py
# Enter keyword: 
# Enter hashtag: 
# Enter username: elonmusk
# Select mode: 1 (TOP)
# Enter number: 200
# → Scrapes 200 tweets from @elonmusk
```

---

## 🔍 Performance

### Speed Benchmarks

**100 tweets:**
- Time: ~2-3 minutes
- Speed: ~40 tweets/minute
- Tabs: 6 parallel

**200 tweets:**
- Time: ~4-6 minutes
- Speed: ~35 tweets/minute
- Tabs: 8 parallel

**500 tweets:**
- Time: ~12-15 minutes
- Speed: ~35 tweets/minute
- Tabs: 8 parallel

### Optimization Techniques

1. **Parallel tabs** - 4-8 simultaneous browsers
2. **API interception** - Faster than DOM parsing
3. **Buffered writing** - Batch CSV writes
4. **Smart scrolling** - 6-8x viewport height
5. **Minimal waits** - 0.3-1.5 second delays

---

## 🛠️ Configuration

### Adjustable Parameters

**In TwitterScraper:**
- `num_tabs` - Number of parallel tabs (auto-calculated)
- `max_scrolls` - Maximum scroll attempts (80-150)
- `max_no_content` - Persistence (8-15 attempts)
- `scroll_multiplier` - Scroll distance (6-8x)

**In main.py:**
- `num_tweets` - Target count (10-500)
- `search_mode` - TOP/LIVE/PEOPLE
- `keyword/hashtag/username` - Search terms

---

## 📝 Summary

This Twitter scraper is a **robust, fast, and feature-rich** tool that:

✅ Scrapes without Twitter API
✅ Uses parallel browsers for speed
✅ Intercepts API for real data
✅ Writes CSV in real-time
✅ Handles 28 data fields
✅ Filters by engagement
✅ Prevents duplicates
✅ Rotates proxies
✅ Uses cookie authentication
✅ Reaches target counts reliably

**Perfect for:** Data analysis, research, monitoring, archiving
