# Twitter/X Scraper - Terminal Edition

A fast, reliable Twitter/X scraper with terminal interface for collecting tweets and saving to CSV.

## 🚀 Quick Start

```bash
python main.py
```

The scraper will prompt you for:
- **Keyword** to search (optional)
- **Hashtag** to search (optional, without #)  
- **Username** to search (optional, without @)
- **Number of tweets** to collect (10-500)

## ✨ Features

- **Terminal Interface**: Clean, interactive command-line interface
- **Flexible Search**: Search by keyword, hashtag, username, or combination
- **Smart Mode Selection**: 
  - 🚀 **TURBO MODE** (50+ tweets): FastCSVHandler with parallel processing
  - 📝 **STANDARD MODE** (<50 tweets): Standard CSVHandler
- **High Quality CSV**: Properly formatted with all tweet data
- **Real-time Progress**: Live updates during scraping
- **Error Handling**: Robust error handling and recovery

## 📊 Output

Creates CSV files in `scraped_data/` folder with:
- Tweet ID, URL, username, display name
- Full tweet text (cleaned and formatted)
- Timestamp, language, tweet type
- Engagement metrics (likes, retweets, replies)
- Hashtags and mentions
- Media URLs and verification status

## 🔧 Requirements

```bash
pip install -r requirements.txt
```

## 💡 Usage Examples

**Search by keyword:**
```
Enter keyword: "artificial intelligence"
Enter hashtag: (press Enter)
Enter username: (press Enter)
Enter number of tweets: 100
```

**Search by hashtag:**
```
Enter keyword: (press Enter)  
Enter hashtag: AI
Enter username: (press Enter)
Enter number of tweets: 50
```

**Search by username:**
```
Enter keyword: (press Enter)
Enter hashtag: (press Enter)
Enter username: elonmusk
Enter number of tweets: 25
```

## ⚡ Performance

- **TURBO MODE**: ~2-3 tweets/second for large targets (50+ tweets)
- **STANDARD MODE**: ~1-2 tweets/second for smaller targets
- **Parallel Processing**: Multi-tab scraping for maximum efficiency
- **Memory Efficient**: Batched CSV writing and smart buffering

## 📁 Project Structure

```
├── main.py                 # Terminal interface
├── scraper/
│   ├── playwright_scraper.py   # Main scraping engine
│   ├── csv_handler.py          # Standard CSV handler  
│   ├── fast_csv_handler.py     # Fast CSV handler for large targets
│   ├── proxy_manager.py        # Proxy rotation
│   └── cookie_loader.py        # Cookie management
├── scraped_data/           # Output CSV files
└── requirements.txt        # Dependencies
```

## 🎯 Success Rate

- **High Success Rate**: Optimized selectors and error handling
- **Anti-Detection**: Cookie loading and proxy rotation
- **Stable Performance**: Tested with targets from 10 to 500 tweets