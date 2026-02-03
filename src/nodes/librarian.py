"""Librarian Node: Deduplication and corroboration using MD5 hashing and Pinecone."""

import uuid
from datetime import datetime
from src.state import NewsState
from src.config import Config
from src.services.database import DatabaseClient
from src.services.pinecone_client import PineconeClient
from src.services.embeddings import EmbeddingService
from src.utils.hashing import generate_md5_hash

# Corroboration threshold - articles between this and duplicate threshold are corroborating
CORROBORATION_THRESHOLD = 0.90


async def librarian_node(state: NewsState) -> NewsState:
    """Node 2: Check for duplicates and corroboration using hash and vector similarity.
    
    Logic:
    1. Generate MD5 hash of raw_persian_text
    2. Check PostgreSQL for exact hash match
    3. Generate embedding
    4. Query Pinecone for similar articles (last 24h)
    5. Three outcomes:
       - similarity >= 0.95: Exact duplicate, skip
       - similarity >= 0.90: Corroboration, link to existing story group
       - similarity < 0.90: New story, create new group
    
    Args:
        state: Current pipeline state
        
    Returns:
        Updated state with is_duplicate flag and story_group_id
    """
    db_client = DatabaseClient()
    pinecone_client = PineconeClient()
    embedding_service = EmbeddingService()
    
    raw_text = state.get("raw_persian_text", "")
    
    if not raw_text:
        state["is_duplicate"] = True
        state["error"] = "No raw text to deduplicate"
        return state
    
    # Generate MD5 hash
    dedupe_hash = generate_md5_hash(raw_text)
    state["dedupe_hash"] = dedupe_hash
    
    # Check PostgreSQL for exact hash match
    await db_client.connect()
    hash_exists = await db_client.check_hash_exists(dedupe_hash)
    
    if hash_exists:
        state["is_duplicate"] = True
        state["error"] = "Exact hash match found in database"
        await db_client.close()
        return state
    
    # Generate embedding
    embedding = await embedding_service.generate_embedding(raw_text)
    state["embedding"] = embedding
    
    # Query Pinecone for similar articles (check for exact duplicates first)
    duplicate_match = await pinecone_client.find_similar(
        embedding=embedding,
        threshold=Config.DEDUPE_SIMILARITY_THRESHOLD,  # 0.95
        time_window_hours=Config.DEDUPE_TIME_WINDOW_HOURS
    )
    
    if duplicate_match:
        state["is_duplicate"] = True
        state["error"] = f"Similar article found (similarity: {duplicate_match['score']:.3f})"
        await db_client.close()
        return state
    
    # Check for corroboration (0.90 <= similarity < 0.95)
    corroboration_match = await pinecone_client.find_corroborating(
        embedding=embedding,
        corroboration_threshold=CORROBORATION_THRESHOLD,
        duplicate_threshold=Config.DEDUPE_SIMILARITY_THRESHOLD,
        time_window_hours=Config.DEDUPE_TIME_WINDOW_HOURS
    )
    
    if corroboration_match:
        # Found a corroborating article - link to its story group
        corroborating_metadata = corroboration_match.get("metadata", {})
        existing_story_group_id = corroborating_metadata.get("story_group_id")
        
        if existing_story_group_id:
            state["story_group_id"] = existing_story_group_id
            state["is_primary"] = False  # Corroborating articles are not primary
            print(f"  → Corroboration detected (similarity: {corroboration_match['score']:.3f})")
            print(f"    Linked to story group: {existing_story_group_id}")
        else:
            # Corroborating article exists but doesn't have a story_group_id yet
            # Create a new group ID and mark this as primary
            new_group_id = str(uuid.uuid4())
            state["story_group_id"] = new_group_id
            state["is_primary"] = True
            print(f"  → Corroboration detected but no existing group - creating: {new_group_id}")
    else:
        # No corroboration - new story, will get a new story_group_id when saved
        state["story_group_id"] = None  # Will be generated in save_article
        state["is_primary"] = True
    
    # Store in Pinecone for future checks
    article_id = f"article_{dedupe_hash}"
    new_story_group_id = state.get("story_group_id") or str(uuid.uuid4())
    state["story_group_id"] = new_story_group_id
    
    metadata = {
        "source_url": state.get("source_url", ""),
        "source_name": state.get("source_name", ""),
        "timestamp": datetime.utcnow().timestamp(),
        "story_group_id": new_story_group_id,
        "dedupe_hash": dedupe_hash
    }
    
    await pinecone_client.upsert_article(
        article_id=article_id,
        embedding=embedding,
        metadata=metadata
    )
    
    state["is_duplicate"] = False
    await db_client.close()
    return state
