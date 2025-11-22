# ⚡ Turbo Mode Configuration

# Performance Settings
TURBO_MODE_ENABLED = True
TURBO_MIN_TWEETS = 50  # Use turbo mode for 50+ tweets
ASYNC_WORKERS = 8      # Number of async workers
BATCH_SIZE = 20        # CSV batch write size
MAX_SCROLLS = 15       # Reduced scroll attempts
SCROLL_DELAY = 0.5     # Faster scroll timing
BROWSER_POOL_SIZE = 3  # Browser pool size

# Speed Optimizations  
FAST_EXTRACTION = True # Use minimal data extraction
SKIP_ENGAGEMENT = True # Skip likes/retweets extraction for speed
MINIMAL_FIELDS = True  # Only extract essential fields

# Expected Performance
# 100 tweets: 45-60 seconds (target: <60s)
# 200 tweets: 90-120 seconds 
# 500 tweets: 3-4 minutes

# Turbo Mode Features:
# ✅ 8 async workers instead of 6 sync tabs
# ✅ Browser pool (reuse instead of create/destroy)  
# ✅ Batch CSV writing (20 tweets at once)
# ✅ Minimal field extraction
# ✅ Faster scroll timing (0.5s vs 1s)
# ✅ Early exit on target reached
# ✅ Reduced max scrolls (15 vs 20)