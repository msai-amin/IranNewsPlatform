"""Proxy manager for handling Iranian geo-fencing."""

import os
from typing import Optional
from urllib.parse import urlparse
from src.config import Config


class ProxyManager:
    """Manages proxy rotation for web scraping."""
    
    def __init__(self):
        """Initialize proxy manager."""
        # Load proxies from environment
        self.iran_proxies = self._parse_proxy_list(
            os.getenv("IRAN_PROXIES", "")
        )
        self.global_proxies = self._parse_proxy_list(
            os.getenv("GLOBAL_PROXIES", "")
        )
        self.current_iran_idx = 0
        self.current_global_idx = 0
    
    def _parse_proxy_list(self, proxy_string: str) -> list[str]:
        """Parse comma-separated proxy list.
        
        Args:
            proxy_string: Comma-separated proxy URLs
            
        Returns:
            List of proxy URLs
        """
        if not proxy_string:
            return []
        return [p.strip() for p in proxy_string.split(",") if p.strip()]
    
    def get_proxy_for_url(self, url: str) -> Optional[dict]:
        """Get appropriate proxy for URL.
        
        Args:
            url: Target URL
            
        Returns:
            Proxy dict for requests/httpx, or None
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Use Iran proxies for .ir domains
        if domain.endswith('.ir'):
            if self.iran_proxies:
                proxy_url = self.iran_proxies[self.current_iran_idx % len(self.iran_proxies)]
                self.current_iran_idx += 1
                return {"http": proxy_url, "https": proxy_url}
        else:
            # Use global proxies for international domains
            if self.global_proxies:
                proxy_url = self.global_proxies[self.current_global_idx % len(self.global_proxies)]
                self.current_global_idx += 1
                return {"http": proxy_url, "https": proxy_url}
        
        return None
    
    def rotate_proxy(self, url: str):
        """Rotate to next proxy (for failover).
        
        Args:
            url: URL that failed
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if domain.endswith('.ir'):
            self.current_iran_idx += 1
        else:
            self.current_global_idx += 1
