def load_cookies(cookie_file='x.com_cookies.txt'):
    """Load cookies from Netscape format file"""
    cookies = []
    
    try:
        with open(cookie_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse Netscape cookie format
                parts = line.split('\t')
                if len(parts) >= 7:
                    domain, _, path, secure, expires, name, value = parts[:7]
                    
                    cookie = {
                        'name': name,
                        'value': value,
                        'domain': domain,
                        'path': path,
                        'expires': int(expires) if expires.isdigit() else -1,
                        'httpOnly': False,
                        'secure': secure == 'TRUE',
                        'sameSite': 'None' if secure == 'TRUE' else 'Lax'
                    }
                    cookies.append(cookie)
        
        print(f"Loaded {len(cookies)} cookies")
        return cookies
    
    except FileNotFoundError:
        print(f"Warning: {cookie_file} not found. Scraping without authentication.")
        return []
