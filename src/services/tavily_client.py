"""Tavily API client for fact-checking and cross-referencing."""

from tavily import TavilyClient as TavilySDK
from src.config import Config


class TavilyClient:
    """Tavily client for fact-checking searches."""
    
    def __init__(self):
        """Initialize Tavily client."""
        self.client = TavilySDK(api_key=Config.TAVILY_API_KEY)
        self.trusted_domains = Config.TRUSTED_DOMAINS
    
    async def fact_check_claim(
        self,
        claim: str,
        source_type: str = "telegram"
    ) -> dict:
        """Fact-check a claim against trusted sources.
        
        Args:
            claim: Claim to verify
            source_type: Type of source (telegram/web)
            
        Returns:
            dict with verification status and notes
        """
        try:
            # Build search query with domain filters
            domain_filter = " OR ".join([f"site:{domain}" for domain in self.trusted_domains])
            query = f"{claim} ({domain_filter})"
            
            # Tavily client is synchronous, wrap in async
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=5,
                    include_domains=self.trusted_domains
                )
            )
            
            results = response.get("results", [])
            
            if not results:
                return {
                    "status": "unverified",
                    "notes": [f"No corroborating sources found for: {claim}"],
                    "sources": []
                }
            
            # Analyze results
            notes = []
            sources = []
            verified_count = 0
            
            for result in results:
                title = result.get("title", "")
                url = result.get("url", "")
                content = result.get("content", "")
                
                sources.append({"title": title, "url": url})
                
                # Check if content supports or contradicts claim
                if any(keyword.lower() in content.lower() for keyword in claim.split()[:3]):
                    verified_count += 1
                    notes.append(f"Corroborated by {title}: {content[:100]}...")
            
            if verified_count >= 2:
                status = "verified"
            elif verified_count == 1:
                status = "unverified"  # Single source, not enough
            else:
                status = "propaganda"  # No matches, likely false
            
            return {
                "status": status,
                "notes": notes,
                "sources": sources,
                "verification_count": verified_count
            }
        except Exception as e:
            return {
                "status": "unverified",
                "notes": [f"Fact-check error: {str(e)}"],
                "sources": []
            }
