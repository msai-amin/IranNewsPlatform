"""Editor Node: Generate AP Style news copy."""

from datetime import datetime
from src.state import NewsState
from src.services.llm import TieredLLMClient


async def editor_node(state: NewsState) -> NewsState:
    """Node 5: Generate final news copy in AP Style.
    
    Logic:
    - Use Editor model (gemini-3-pro or claude-3-5-sonnet)
    - Generate AP Style article
    - Proper attribution for unverified claims
    
    Args:
        state: Current pipeline state
        
    Returns:
        Updated state with final_copy
    """
    llm_client = TieredLLMClient()
    
    english_translation = state.get("english_translation", "")
    fact_check_status = state.get("fact_check_status", "unverified")
    fact_check_notes = state.get("fact_check_notes", [])
    
    if not english_translation:
        state["error"] = "No translation available for editing"
        return state
    
    # Generate news copy
    final_copy = await llm_client.generate_news_copy(
        english_translation=english_translation,
        fact_check_notes=fact_check_notes,
        fact_check_status=fact_check_status
    )
    
    state["final_copy"] = final_copy
    state["processed_at"] = datetime.utcnow().isoformat()
    
    return state
