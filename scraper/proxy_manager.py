import random
from typing import List, Optional

class ProxyManager:
    def __init__(self, proxy_file='proxies.txt'):
        self.proxies = []
        self.failed_proxies = set()
        self.current_index = 0
        self.load_proxies(proxy_file)
    
    def load_proxies(self, proxy_file):
        """Load proxies from file in format: ip:port:username:password"""
        try:
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.proxies.append(line)
            print(f"Loaded {len(self.proxies)} proxies")
        except FileNotFoundError:
            print(f"Warning: {proxy_file} not found. Running without proxies.")
    
    def get_next_proxy(self) -> Optional[dict]:
        """Alias for get_proxy for compatibility"""
        return self.get_proxy()
    
    def get_proxy(self) -> Optional[dict]:
        """Get next available proxy in round-robin fashion"""
        if not self.proxies:
            return None
        
        attempts = 0
        while attempts < len(self.proxies):
            proxy_str = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            
            if proxy_str not in self.failed_proxies:
                return self.parse_proxy(proxy_str)
            
            attempts += 1
        
        # All proxies failed, reset and try again
        print("All proxies failed, resetting failed list...")
        self.failed_proxies.clear()
        return self.parse_proxy(self.proxies[0]) if self.proxies else None
    
    def parse_proxy(self, proxy_str: str) -> dict:
        """Parse proxy string into Playwright format"""
        parts = proxy_str.split(':')
        if len(parts) == 4:
            ip, port, username, password = parts
            return {
                'server': f'http://{ip}:{port}',
                'username': username,
                'password': password
            }
        elif len(parts) == 2:
            ip, port = parts
            return {
                'server': f'http://{ip}:{port}'
            }
        return None
    
    def mark_failed(self, proxy_dict: dict):
        """Mark a proxy as failed"""
        if proxy_dict:
            server = proxy_dict.get('server', '')
            # Find original proxy string
            for proxy_str in self.proxies:
                if server in proxy_str:
                    self.failed_proxies.add(proxy_str)
                    print(f"Marked proxy as failed: {server}")
                    break
