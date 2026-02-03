"""State schema for LangGraph pipeline."""

from typing import TypedDict, Literal, Optional


class NewsState(TypedDict, total=False):
    """State schema for news processing pipeline.
    
    Fields are optional (total=False) to allow incremental updates
    as the state flows through the graph nodes.
    """
    source_url: str
    source_type: Literal['telegram', 'web']
    source_name: str                              # Channel name or domain
    raw_persian_text: str
    english_translation: str
    bias_score: int                               # 1-10
    fact_check_status: Literal['verified', 'propaganda', 'unverified', 'pending']
    fact_check_notes: list[str]
    dedupe_hash: str
    embedding: list[float]
    is_duplicate: bool
    is_news: bool
    final_copy: str
    processed_at: str
    error: Optional[str]
    # Cross-source corroboration fields
    story_group_id: Optional[str]                 # UUID linking corroborating articles
    is_primary: bool                              # True if this is the primary article in a group
    # Dev dashboard: run_id for agent log recording
    run_id: Optional[str]