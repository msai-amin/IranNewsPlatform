"""Translator Node: Persian-English literal translation."""

from src.state import NewsState
from src.services.llm import TieredLLMClient


async def translator_node(state: NewsState) -> NewsState:
    """Node 3: Translate Persian text to English (literal, preserving tone).
    
    Logic:
    - Use Translator model (gemini-3-flash)
    - Literal translation (no summarization)
    - Resolve drop-pronouns
    - Preserve original tone/word choice
    
    Args:
        state: Current pipeline state
        
    Returns:
        Updated state with english_translation
    """
    llm_client = TieredLLMClient()
    
    raw_persian = state.get("raw_persian_text", "")
    
    if not raw_persian:
        state["error"] = "No Persian text to translate"
        return state
    
    # Translate using Translator model
    translation = await llm_client.translate_persian(raw_persian)
    
    state["english_translation"] = translation
    return state
