"""Hashing utilities for deduplication."""

import hashlib


def generate_md5_hash(text: str) -> str:
    """Generate MD5 hash for text deduplication.
    
    Args:
        text: Text to hash
        
    Returns:
        MD5 hash hex string
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()
