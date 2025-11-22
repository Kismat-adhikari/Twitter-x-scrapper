# Quick Start: Getting Tweets with Engagement

## The Problem
Your scraper is returning tweets with **0 likes, 0 retweets, 0 replies** because it was fetching the newest tweets, which haven't had time to get engagement yet.

## The Solution
Use **TOP mode** (now the default) to get popular tweets with actual engagement.

---

## How to Use

### Run the scraper:
```bash
python main.py
```

### When prompted for search mode:
```
📊 Search Mode (affects engagement levels):
  1. TOP - Popular tweets with high engagement (recommended)
  2. LIVE - Latest tweets (may have low/zero engagement)
  3. PEOPLE - From verified accounts (usually higher engagement)

Select mode (1/2/3) [default: 1]:
```

**Just press Enter** or type `1` for TOP mode (recommended)

---

## What Each Mode Does

### 1️⃣ TOP Mode (Recommended)
✅ Returns tweets ranked by popularity  
✅ Minimum 10 likes guaranteed  
✅ Best for getting engaged content  

**Use when:** You want tweets people are actually interacting with

### 2️⃣ LIVE Mode
⚠️ Returns newest tweets chronologically  
⚠️ May have ZERO engagement  
⚠️ Good for real-time monitoring only  

**Use when:** You need the absolute latest tweets

### 3️⃣ PEOPLE Mode
✓ Returns tweets from verified accounts  
✓ Usually higher quality  
✓ Better engagement than LIVE  

**Use when:** You want content from established accounts

---

## Example Usage

### For Popular AI Tweets:
```
Enter keyword(s): AI technology
Enter hashtag: 
Enter username: 
Select mode: 1 (or just press Enter)
Number of tweets: 50
```

Result: 50 popular AI tweets with likes, retweets, and replies

### For Latest Crypto News:
```
Enter keyword(s): 
Enter hashtag: crypto
Enter username: 
Select mode: 2
Number of tweets: 30
```

Result: 30 newest crypto tweets (may have low engagement)

### For Verified Tech Influencers:
```
Enter keyword(s): technology
Enter hashtag: 
Enter username: 
Select mode: 3
Number of tweets: 40
```

Result: 40 tweets from verified accounts about technology

---

## Advanced Tips

### Get Even Higher Engagement
Add `min_faves:50` to your keyword:
```
Enter keyword(s): AI min_faves:50
```
This requires at least 50 likes per tweet.

### Combine Filters
```
Enter keyword(s): crypto min_faves:100 min_retweets:20
```
This requires 100+ likes AND 20+ retweets.

### Target Specific Accounts
```
Enter keyword(s): from:elonmusk
```
Gets tweets from a specific user.

---

## Testing

Compare all three modes:
```bash
python test_engagement_modes.py
```

This will scrape 20 tweets in each mode and show you the engagement statistics.

---

## Troubleshooting

**Still getting 0 engagement?**
1. Make sure you selected mode `1` (TOP)
2. Try a more popular keyword (e.g., "AI", "crypto", "technology")
3. Add `min_faves:20` to your keyword for even higher engagement

**Not finding enough tweets?**
1. Use broader search terms
2. Lower the engagement filter: `min_faves:5`
3. Try LIVE mode if you need more results

---

## Summary

✅ **Default is now TOP mode** - automatically filters for engagement  
✅ **Press Enter** at the mode prompt to use TOP mode  
✅ **Check your CSV** - tweets should now have likes/retweets/replies > 0  

For more details, see [ENGAGEMENT_FILTERING_GUIDE.md](ENGAGEMENT_FILTERING_GUIDE.md)
