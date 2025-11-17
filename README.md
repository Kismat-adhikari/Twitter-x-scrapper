# Twitter Scraper with Flask & Playwright

A full-stack Twitter scraper using Flask backend, Playwright for scraping, and HTML/CSS/JS frontend.

## Features
- Keyword, hashtag, username, and tweet URL scraping
- **English tweets only** - automatically filters by language (lang="en")
- **Only scrapes original tweets** - skips replies and retweets
- Parallel scraping with 4 tabs for faster results
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

## Usage
1. Fill in at least one search field (keyword, hashtag, username, or tweet URL)
2. Select number of tweets to scrape
3. Click "Start Scraping"
4. Wait for completion
5. Check `scraped_data/` folder for CSV files

## Notes
- Scraping runs in background thread
- 4 parallel tabs by default (configurable in code)
- Each tab uses a different proxy
- Results are deduplicated by tweet ID
- Cookies provide authentication for better access
