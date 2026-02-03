"""Pinecone vector database client for deduplication."""

import asyncio
import time
from typing import Optional
from pinecone import Pinecone, ServerlessSpec
from src.config import Config


class PineconeClient:
    """Pinecone client for vector similarity search.
    
    Uses namespaces for data isolation (MANDATORY in latest SDK).
    All operations use the 'articles' namespace for deduplication.
    """
    
    # Default namespace for article deduplication
    DEFAULT_NAMESPACE = "articles"
    
    def __init__(self):
        """Initialize Pinecone client."""
        if not Config.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is required. Please set it in your .env file.")
        
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index_name = Config.PINECONE_INDEX_NAME
        self.namespace = self.DEFAULT_NAMESPACE
        
        # Get or create index (idempotent)
        try:
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            if self.index_name not in existing_indexes:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=Config.EMBEDDING_DIMENSION,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=Config.PINECONE_ENVIRONMENT
                    )
                )
                # Wait for index to be ready
                import time
                time.sleep(5)
        except Exception as e:
            print(f"Warning: Could not verify/create index: {e}")
            # Continue anyway - index might already exist
        
        self.index = self.pc.Index(self.index_name)
    
    async def find_similar(
        self,
        embedding: list[float],
        threshold: float = 0.95,
        top_k: int = 5,
        time_window_hours: int = 24,
        namespace: Optional[str] = None
    ) -> Optional[dict]:
        """Find similar articles within time window.
        
        Args:
            embedding: Query embedding vector
            threshold: Minimum similarity score
            top_k: Number of results to return
            time_window_hours: Only check articles from last N hours
            namespace: Namespace to search (defaults to 'articles')
            
        Returns:
            Most similar match if above threshold, else None
        """
        if namespace is None:
            namespace = self.namespace
            
        try:
            # Query Pinecone (Pinecone client is synchronous but we wrap in async)
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.index.query(
                    namespace=namespace,  # MANDATORY: namespace required
                    vector=embedding,
                    top_k=top_k,
                    include_metadata=True
                )
            )
            
            # Filter by threshold and time window
            cutoff_time = time.time() - (time_window_hours * 3600)
            
            for match in results.matches:
                if match.score >= threshold:
                    # Check timestamp if available
                    metadata = match.metadata or {}
                    article_time = metadata.get("timestamp", 0)
                    if article_time >= cutoff_time:
                        return {
                            "id": match.id,
                            "score": match.score,
                            "metadata": metadata
                        }
            
            return None
        except Exception as e:
            print(f"Pinecone query error: {e}")
            return None
    
    async def find_corroborating(
        self,
        embedding: list[float],
        corroboration_threshold: float = 0.90,
        duplicate_threshold: float = 0.95,
        top_k: int = 5,
        time_window_hours: int = 24,
        namespace: Optional[str] = None
    ) -> Optional[dict]:
        """Find corroborating articles (similar but not duplicate).
        
        Args:
            embedding: Query embedding vector
            corroboration_threshold: Minimum similarity for corroboration (default 0.90)
            duplicate_threshold: Threshold above which is considered duplicate (default 0.95)
            top_k: Number of results to return
            time_window_hours: Only check articles from last N hours
            namespace: Namespace to search (defaults to 'articles')
            
        Returns:
            Best corroborating match (0.90 <= score < 0.95) if found, else None
        """
        if namespace is None:
            namespace = self.namespace
            
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.index.query(
                    namespace=namespace,
                    vector=embedding,
                    top_k=top_k,
                    include_metadata=True
                )
            )
            
            cutoff_time = time.time() - (time_window_hours * 3600)
            
            for match in results.matches:
                # Corroboration: similar but not duplicate
                if corroboration_threshold <= match.score < duplicate_threshold:
                    metadata = match.metadata or {}
                    article_time = metadata.get("timestamp", 0)
                    if article_time >= cutoff_time:
                        return {
                            "id": match.id,
                            "score": match.score,
                            "metadata": metadata
                        }
            
            return None
        except Exception as e:
            print(f"Pinecone corroboration query error: {e}")
            return None
    
    async def upsert_article(
        self,
        article_id: str,
        embedding: list[float],
        metadata: dict,
        namespace: Optional[str] = None
    ):
        """Store article embedding in Pinecone.
        
        Args:
            article_id: Unique article identifier
            embedding: Article embedding vector
            metadata: Article metadata (source, timestamp, etc.)
            namespace: Namespace to upsert to (defaults to 'articles')
            
        Note:
            After upserting, wait 10+ seconds before querying for best results.
        """
        if namespace is None:
            namespace = self.namespace
            
        try:
            # Ensure metadata is flat (no nested objects)
            flat_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool, list)):
                    flat_metadata[key] = value
                else:
                    # Convert non-supported types to string
                    flat_metadata[key] = str(value)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.index.upsert(
                    namespace=namespace,  # MANDATORY: namespace required
                    vectors=[{
                        "id": article_id,
                        "values": embedding,
                        "metadata": flat_metadata
                    }]
                )
            )
        except Exception as e:
            print(f"Pinecone upsert error: {e}")
            raise
