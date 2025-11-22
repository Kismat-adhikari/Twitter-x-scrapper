# Twitter Scraper with Flask & Playwright

A full-stack Twitter scraper using Flask backend, Playwright for scraping, and HTML/CSS/JS frontend.

> **🔥 CRITICAL FIX:** All engagement showing 0? See [REAL_ENGAGEMENT_FIX.md](REAL_ENGAGEMENT_FIX.md) - Now extracts REAL likes, retweets, replies!  
> **📊 Search Modes:** [QUICK_START_ENGAGEMENT.md](QUICK_START_ENGAGEMENT.md) - Get popular tweets with high engagement  
> **📚 Full Documentation:** [ENGAGEMENT_DOCS_INDEX.md](ENGAGEMENT_DOCS_INDEX.md)

## Features
- Keyword, hashtag, username, and tweet URL scraping
- **3 Search Modes for Engagement Filtering:**
  - **TOP Mode** (default) - Popular tweets with high engagement
  - **LIVE Mode** - Latest tweets (chronological)
  - **PEOPLE Mode** - Tweets from verified accounts only
- **English tweets only** - automatically filters by language (lang="en")
- **Only scrapes original tweets** - skips replies and retweets
- Parallel scraping with dynamic tab count for optimal speed
- **Real-time CSV writing** - tweets saved immediately as scraped
- Proxy rotation with automatic failover
- Cookie-based authentication
- Thread-safe duplicate prevention
- Real-time status updates with emojis

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers
```bash
playwright install chromium
```

### 3. Run the Application
```bash
python app.py
```

### 4. Open Browser
Navigate to: http://localhost:5000

## Files Structure
- `app.py` - Flask application
- `scraper/playwright_scraper.py` - Main scraping logic
- `scraper/proxy_manager.py` - Proxy rotation
- `scraper/cookie_loader.py` - Cookie authentication
- `scraper/csv_handler.py` - CSV export
- `proxies.txt` - Your proxy list
- `x.com_cookies.txt` - Your Twitter cookies
- `scraped_data/` - Output CSV files

## Quick Start

### 1. Set Up Authentication (REQUIRED for real engagement)

**Get your Twitter cookies:**
```bash
# See COOKIE_SETUP_GUIDE.md for detailed instructions
```

1. Log in to Twitter/X in your browser
2. Open Developer Tools (F12) → Application → Cookies → x.com
3. Copy `auth_token` and `ct0` values
4. Create `x.com_cookies.txt` in Netscape format

**Without cookies:** All engagement will show as 0  
**With cookies:** Real likes, retweets, replies! ✅

See [COOKIE_SETUP_GUIDE.md](COOKIE_SETUP_GUIDE.md) for step-by-step instructions.

### 2. Run the Scraper

```bash
python main.py
```

Follow the prompts:
1. Enter keyword(s), hashtag(s), or username
2. **Select search mode:**
   - `1` - TOP mode (popular tweets with engagement) - **Recommended**
   - `2` - LIVE mode (latest tweets, may have zero engagement)
   - `3` - PEOPLE mode (verified accounts only)
3. Enter number of tweets to scrape (10-500)
4. Confirm and wait for completion
5. Check `scraped_data/` folder for CSV files

### 3. Verify Real Engagement

```bash
python test_real_engagement.py
```

This will verify that engagement metrics are being extracted correctly.

### Web Interface
```bash
python app.py
```
Then navigate to http://localhost:5000

## Engagement Filtering

**Problem:** Getting tweets with 0 likes, 0 retweets, 0 replies?

**Solution:** Use **TOP mode** (default) which filters for popular tweets with actual engagement.

See [ENGAGEMENT_FILTERING_GUIDE.md](ENGAGEMENT_FILTERING_GUIDE.md) for detailed information about:
- How each search mode works
- When to use each mode
- Advanced Twitter search operators
- Tips for best results

### Quick Comparison

| Mode | Engagement Level | Best For |
|------|-----------------|----------|
| TOP | High (min 10 likes) | Popular content, trending topics |
| LIVE | Variable (may be 0) | Real-time monitoring, breaking news |
| PEOPLE | Medium-High | Verified accounts, influencers |

### Testing Engagement Modes
```bash
python test_engagement_modes.py
```
This will compare all three modes and show engagement statistics.

## Notes
- Scraping runs in background thread
- 4 parallel tabs by default (configurable in code)
- Each tab uses a different proxy
- Results are deduplicated by tweet ID
- Cookies provide authentication for better access
