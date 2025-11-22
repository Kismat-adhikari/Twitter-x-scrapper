#!/usr/bin/env python3
"""Quick script to verify cookies are loaded correctly"""

from scraper.cookie_loader import load_cookies

print("🔍 Checking Cookie Setup...")
print("=" * 60)

cookies = load_cookies()

if not cookies:
    print("❌ FAILED: No cookies loaded!")
    print("   Make sure x.com_cookies.txt exists and has valid cookies.")
    exit(1)

print(f"✅ Loaded {len(cookies)} cookies")
print()

# Check for required cookies
auth_token = None
ct0 = None

for cookie in cookies:
    if cookie['name'] == 'auth_token':
        auth_token = cookie['value']
    elif cookie['name'] == 'ct0':
        ct0 = cookie['value']

print("📋 Required Cookies:")
print("-" * 60)

if auth_token:
    print(f"✅ auth_token: Found ({len(auth_token)} chars)")
    print(f"   Value: {auth_token[:20]}...{auth_token[-20:]}")
else:
    print("❌ auth_token: MISSING!")

print()

if ct0:
    print(f"✅ ct0: Found ({len(ct0)} chars)")
    print(f"   Value: {ct0[:20]}...{ct0[-20:]}")
else:
    print("❌ ct0: MISSING!")

print()
print("=" * 60)

if auth_token and ct0:
    print("✅ SUCCESS: All required cookies are present!")
    print()
    print("You're ready to scrape with real engagement metrics!")
    print()
    print("Next steps:")
    print("  1. Run: python main.py")
    print("  2. Select TOP mode (press Enter)")
    print("  3. Enter a popular keyword (e.g., 'AI')")
    print("  4. Check CSV for real engagement numbers!")
else:
    print("❌ FAILED: Missing required cookies!")
    print()
    print("Please follow COOKIE_SETUP_GUIDE.md to get:")
    print("  - auth_token")
    print("  - ct0")
