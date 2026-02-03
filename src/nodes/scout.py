"""Scout Node: Ingestion & Triage using gemini-2.5-flash-lite."""

from datetime import datetime
from src.state import NewsState
from src.config import Config
from src.services.llm import TieredLLMClient
from src.utils.persian import clean_persian_text


async def scout_node(state: NewsState) -> NewsState:
    """Node 1: Filter and classify incoming content as news.
    
    Logic:
    - Discard if text < MIN_TEXT_LENGTH
    - Use Scout model to classify: Is this news?
    - Set is_news flag
    
    Args:
        state: Current pipeline state
        
    Returns:
        Updated state with is_news flag
    """
    llm_client = TieredLLMClient()
    
    # Extract raw text
    raw_text = state.get("raw_persian_text", "")
    
    # Clean text
    cleaned_text = clean_persian_text(raw_text)
    
    # Check minimum length
    if len(cleaned_text) < Config.MIN_TEXT_LENGTH:
        state["is_news"] = False
        state["error"] = f"Text too short ({len(cleaned_text)} < {Config.MIN_TEXT_LENGTH})"
        return state
    
    # Classify using Scout model
    classification = await llm_client.scout_classify(cleaned_text)
    
    state["is_news"] = classification.get("is_news", False)
    state["raw_persian_text"] = cleaned_text
    
    if not state["is_news"]:
        state["error"] = classification.get("error") or "Not classified as news"
    
    return state
