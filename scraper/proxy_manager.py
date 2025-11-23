import random
import threading
from typing import List, Optional

class ProxyManager:
    def __init__(self, proxy_file='proxies.txt', rotation_count=3):  # Rotate more frequently
        self.proxies = []
        self.failed_proxies = set()
        self.current_index = 0
        self.rotation_count = rotation_count  # Rotate after N uses
        self.usage_count = 0  # Track how many times current proxy has been used
        self.proxy_usage = {}  # Track usage per proxy
        self.lock = threading.Lock()  # Thread safety for parallel tabs
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
        """Get next available proxy with proper rotation for parallel tabs"""
        if not self.proxies:
            return None
        
        with self.lock:
            # Find the least used, non-failed proxy
            available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
            if not available_proxies:
                # Reset failed proxies if all are failed
                print("All proxies failed, resetting failed list...")
                self.failed_proxies.clear()
                available_proxies = self.proxies[:]
            
            # Sort by usage count (ascending) to get least used proxy
            available_proxies.sort(key=lambda p: self.proxy_usage.get(p, 0))
            
            # Get the least used proxy
            selected_proxy_str = available_proxies[0]
            
            # Update usage count
            self.proxy_usage[selected_proxy_str] = self.proxy_usage.get(selected_proxy_str, 0) + 1
            
            proxy_dict = self.parse_proxy(selected_proxy_str)
            if proxy_dict:
                proxy_dict['_usage_count'] = self.proxy_usage[selected_proxy_str]
                proxy_dict['_proxy_string'] = selected_proxy_str  # For failure tracking
                print(f"Assigned proxy {selected_proxy_str.split(':')[0]} (usage: {self.proxy_usage[selected_proxy_str]})")
            
            return proxy_dict
    
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
    
    def get_random_proxy(self) -> Optional[dict]:
        """Get a random proxy from available proxies"""
        if not self.proxies:
            return None
        
        with self.lock:
            available_proxies = [p for p in self.proxies if p not in self.failed_proxies]
            if not available_proxies:
                # Reset if all failed
                self.failed_proxies.clear()
                available_proxies = self.proxies[:]
            
            if available_proxies:
                selected_proxy_str = random.choice(available_proxies)
                proxy_dict = self.parse_proxy(selected_proxy_str)
                if proxy_dict:
                    proxy_dict['_proxy_string'] = selected_proxy_str
                return proxy_dict
            
        return None
    
    def reset_usage_counts(self):
        """Reset all proxy usage counts"""
        with self.lock:
            self.proxy_usage.clear()
            print("Reset all proxy usage counts")
    
    def mark_failed(self, proxy_dict: dict):
        """Mark a proxy as failed"""
        if proxy_dict:
            with self.lock:
                proxy_string = proxy_dict.get('_proxy_string')
                if proxy_string:
                    self.failed_proxies.add(proxy_string)
                    print(f"Marked proxy as failed: {proxy_string.split(':')[0]}")
                else:
                    # Fallback method
                    server = proxy_dict.get('server', '')
                    for proxy_str in self.proxies:
                        if server in proxy_str:
                            self.failed_proxies.add(proxy_str)
                            print(f"Marked proxy as failed: {server}")
                            break
