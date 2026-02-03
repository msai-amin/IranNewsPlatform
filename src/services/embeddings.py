"""Embedding generation for vector similarity."""

import os
from openai import AsyncOpenAI
from src.config import Config


class EmbeddingService:
    """Generate embeddings for text using OpenAI's embedding model."""
    
    def __init__(self):
        """Initialize embedding client."""
        # Using OpenAI's embedding model (text-embedding-3-small)
        # Note: You may want to use a free/open-source alternative
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        self.model = Config.EMBEDDING_MODEL
        self.dimension = Config.EMBEDDING_DIMENSION
    
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (list of floats)
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimension
            )
            return response.data[0].embedding
        except Exception as e:
            # Fallback: return zero vector (will prevent matches)
            print(f"Embedding error: {e}")
            return [0.0] * self.dimension
