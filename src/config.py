"""Configuration and environment settings."""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # LLM API Keys
    GOOGLE_AI_API_KEY: str = os.getenv("GOOGLE_AI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Model Names (valid Gemini API model codes)
    MODEL_SCOUT: str = "gemini-2.5-flash-lite"
    MODEL_TRANSLATOR: str = "gemini-3-flash-preview"
    MODEL_ANALYST: str = "gemini-3-flash-preview"
    MODEL_EDITOR: str = os.getenv("MODEL_EDITOR", "gemini-2.5-pro")  # or gemini-3-pro-preview, claude-3-5-sonnet
    
    # Database
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")
    _db = os.getenv("DATABASE_URL", "")
    DATABASE_URL: Optional[str] = _db if _db and "host:port" not in _db else None  # PostgreSQL
    
    # Pinecone
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "iran-news")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    
    # Tavily
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    
    # Telegram
    TELEGRAM_API_ID: str = os.getenv("TELEGRAM_API_ID", "")
    TELEGRAM_API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    TELEGRAM_SESSION_STRINGS: list[str] = os.getenv("TELEGRAM_SESSION_STRINGS", "").split(",") if os.getenv("TELEGRAM_SESSION_STRINGS") else []
    
    # Firecrawl
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")
    
    # Redis (for session management)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Processing thresholds
    MIN_TEXT_LENGTH: int = 50
    DEDUPE_SIMILARITY_THRESHOLD: float = 0.95
    DEDUPE_TIME_WINDOW_HOURS: int = 24
    
    # Trusted domains for fact-checking
    TRUSTED_DOMAINS: list[str] = [
        "bbc.com",
        "reuters.com",
        "iranintl.com",
        "dw.com",
        "ap.org"
    ]
    
    # State media identifiers (for bias detection)
    STATE_MEDIA_KEYWORDS: list[str] = [
        "fars",
        "tasnim",
        "irna",
        "irib",
        "khabaronline"
    ]
    
    # Embedding model
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536
