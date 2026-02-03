"""Persian text utilities."""

import re


def clean_persian_text(text: str) -> str:
    """Clean Persian text for processing.
    
    Args:
        text: Raw Persian text
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Remove Telegram-specific formatting
    text = re.sub(r'@\w+', '', text)  # Remove mentions
    return text.strip()


def is_state_media(source_name: str) -> bool:
    """Check if source is state-controlled media.
    
    Args:
        source_name: Source name or domain
        
    Returns:
        True if state media
    """
    from src.config import Config
    source_lower = source_name.lower()
    return any(keyword in source_lower for keyword in Config.STATE_MEDIA_KEYWORDS)
