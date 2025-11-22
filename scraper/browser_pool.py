from playwright.sync_api import sync_playwright
import threading
from queue import Queue
import time

class BrowserPool:
    def __init__(self, pool_size=3, proxy_manager=None):
        self.pool_size = pool_size
        self.proxy_manager = proxy_manager
        self.browsers = Queue()
        self.playwright = None
        self.lock = threading.Lock()
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize browser pool"""
        self.playwright = sync_playwright().start()
        
        for i in range(self.pool_size):
            proxy = self.proxy_manager.get_proxy() if self.proxy_manager else None
            browser = self.playwright.chromium.launch(
                headless=True,
                proxy=proxy,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-gpu'
                ]
            )
            self.browsers.put(browser)
    
    def get_browser(self):
        """Get browser from pool"""
        return self.browsers.get()
    
    def return_browser(self, browser):
        """Return browser to pool"""
        self.browsers.put(browser)
    
    def close_all(self):
        """Close all browsers and cleanup"""
        while not self.browsers.empty():
            browser = self.browsers.get()
            try:
                browser.close()
            except:
                pass
        if self.playwright:
            self.playwright.stop()