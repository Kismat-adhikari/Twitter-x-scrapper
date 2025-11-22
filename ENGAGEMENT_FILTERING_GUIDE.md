# Twitter/X Scraper - Engagement Filtering Guide

## Problem
The scraper was returning tweets with zero engagement (0 likes, 0 retweets, 0 replies) because it was using Twitter's "Latest" feed, which shows the most recent tweets regardless of popularity.

## Solution
The scraper now includes **3 search modes** that control which tweets are returned based on engagement levels:

---

## Search Modes

### 1. TOP Mode (Recommended) 📊
**Best for: Getting tweets with actual engagement**

- Returns tweets ranked by popularity and engagement
- Automatically adds `min_faves:10` filter (minimum 10 likes)
- Uses Twitter's `f=top` parameter
- **Result:** Tweets with proven engagement (likes, retweets, replies)

**When to use:**
- You want tweets that people are actually interacting with
- You're analyzing trending topics or popular content
- You need engagement metrics for analysis

### 2. LIVE Mode 🔴
**Best for: Real-time monitoring**

- Returns the most recent tweets chronologically
- No engagement filtering
- Uses Twitter's `f=live` parameter
- **Result:** May include brand new tweets with zero engagement

**When to use:**
- You need the absolute latest tweets
- You're monitoring breaking news or events
- Engagement doesn't matter for your use case

**⚠️ Warning:** This mode will likely return tweets with 0 likes/retweets/replies

### 3. PEOPLE Mode ✓
**Best for: Quality content from verified accounts**

- Returns tweets from verified accounts only
- Adds `filter:verified` to search query
- Uses Twitter's `f=user` parameter
- **Result:** Tweets from verified users (usually higher engagement)

**When to use:**
- You want content from established accounts
- You're researching influencers or brands
- You need higher quality, more reliable content

---

## How to Use

When you run the scraper, you'll see this prompt:

```
📊 Search Mode (affects engagement levels):
  1. TOP - Popular tweets with high engagement (recommended)
  2. LIVE - Latest tweets (may have low/zero engagement)
  3. PEOPLE - From verified accounts (usually higher engagement)

Select mode (1/2/3) [default: 1]:
```

Simply enter:
- `1` or press Enter for TOP mode (recommended)
- `2` for LIVE mode
- `3` for PEOPLE mode

---

## Advanced: Twitter Search Operators

The scraper also supports Twitter's advanced search operators. You can combine these with your keywords:

### Engagement Filters
- `min_faves:50` - Minimum 50 likes
- `min_retweets:10` - Minimum 10 retweets
- `min_replies:5` - Minimum 5 replies

### Account Filters
- `filter:verified` - Only verified accounts
- `from:username` - From specific user
- `to:username` - Replies to specific user

### Content Filters
- `filter:links` - Only tweets with links
- `filter:media` - Only tweets with images/videos
- `filter:videos` - Only tweets with videos

### Date Filters
- `since:2024-01-01` - Tweets after this date
- `until:2024-12-31` - Tweets before this date

### Example Queries
```
AI technology min_faves:100
#crypto filter:verified min_retweets:50
machine learning filter:links since:2024-11-01
```

---

## Technical Details

### What Changed

**Before:**
```python
return f'https://x.com/search?q={encoded_query}&src=typed_query&f=live'
```

**After:**
```python
# TOP mode
return f'https://x.com/search?q={encoded_query} min_faves:10&src=typed_query&f=top'

# LIVE mode
return f'https://x.com/search?q={encoded_query}&src=typed_query&f=live'

# PEOPLE mode
return f'https://x.com/search?q={encoded_query} filter:verified&src=typed_query&f=user'
```

### URL Parameters
- `f=top` - Sorts by engagement/popularity
- `f=live` - Sorts by recency (chronological)
- `f=user` - Filters to people/accounts

---

## Testing

To test the engagement filtering:

1. Run the scraper with TOP mode:
   ```bash
   python main.py
   ```

2. Enter a popular topic (e.g., "AI", "crypto", "technology")

3. Select mode `1` (TOP)

4. Check the CSV output - tweets should have engagement metrics > 0

5. Compare with LIVE mode to see the difference

---

## Tips for Best Results

1. **Use TOP mode by default** - It's the most reliable for getting engaged content

2. **Combine with popular hashtags** - Popular hashtags naturally have more engagement

3. **Target verified accounts** - Use PEOPLE mode or add `filter:verified` to your keywords

4. **Add minimum engagement filters** - Add `min_faves:50` to your keyword for even higher engagement

5. **Search trending topics** - Topics that are currently trending will have more engagement

6. **Avoid very niche queries** - Extremely specific searches may have limited engagement

---

## Troubleshooting

**Still getting tweets with 0 engagement?**

1. Check if you're using TOP mode (not LIVE)
2. Try adding `min_faves:20` to your keyword
3. Use more popular/trending search terms
4. Try PEOPLE mode for verified accounts only
5. Check if the tweets are very recent (may not have engagement yet)

**Not finding enough tweets?**

1. Lower the minimum engagement filter (use `min_faves:5` instead of `min_faves:10`)
2. Use broader search terms
3. Remove date filters if you're using them
4. Try LIVE mode if you need more results

---

## Summary

The scraper now defaults to **TOP mode** which returns popular tweets with actual engagement. This solves the issue of getting tweets with 0 likes/retweets/replies. You can still use LIVE mode if you need the latest tweets, but be aware they may have zero engagement if they're brand new.
