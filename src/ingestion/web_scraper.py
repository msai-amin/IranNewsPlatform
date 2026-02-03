"""Web scraper using Firecrawl for clean Markdown extraction."""

from typing import Optional
from firecrawl import FirecrawlApp
from src.config import Config
from src.services.proxy_manager import ProxyManager


class WebScraper:
    """Scrapes web articles using Firecrawl."""
    
    def __init__(self):
        """Initialize Firecrawl client."""
        self.client = FirecrawlApp(api_key=Config.FIRECRAWL_API_KEY)
        self.proxy_manager = ProxyManager()
    
    async def scrape_url(self, url: str) -> Optional[dict]:
        """Scrape article from URL.
        
        Args:
            url: Article URL
            
        Returns:
            dict with 'content' (markdown) and 'metadata', or None on error
        """
        try:
            # Select proxy based on domain
            proxy = self.proxy_manager.get_proxy_for_url(url)
            
            # Scrape with Firecrawl
            result = self.client.scrape_url(
                url,
                params={
                    "formats": ["markdown"],
                    "onlyMainContent": True
                }
            )
            
            if result and result.get("success"):
                return {
                    "content": result.get("markdown", ""),
                    "metadata": result.get("metadata", {}),
                    "url": url
                }
            
            return None
        except Exception as e:
            print(f"Firecrawl scrape error for {url}: {e}")
            return None
