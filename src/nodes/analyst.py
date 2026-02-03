"""Analyst Node: Fact-checking using Tavily and claim extraction."""

from src.state import NewsState
from src.services.llm import TieredLLMClient
from src.services.tavily_client import TavilyClient
from src.utils.persian import is_state_media


async def analyst_node(state: NewsState) -> NewsState:
    """Node 4: Fact-check claims using Tavily and cross-reference.
    
    Logic:
    1. Extract key claims from translation
    2. If state media, verify claims using Tavily
    3. Cross-reference with trusted domains
    4. Update fact_check_status and notes
    
    Args:
        state: Current pipeline state
        
    Returns:
        Updated state with fact_check_status and notes
    """
    llm_client = TieredLLMClient()
    tavily_client = TavilyClient()
    
    english_text = state.get("english_translation", "")
    source_name = state.get("source_name", "")
    
    if not english_text:
        state["fact_check_status"] = "unverified"
        state["fact_check_notes"] = ["No translation available for fact-checking"]
        return state
    
    # Extract claims
    claims = await llm_client.extract_claims(english_text)
    
    if not claims:
        state["fact_check_status"] = "unverified"
        state["fact_check_notes"] = ["No extractable claims found"]
        return state
    
    # Check if source is state media (affects bias score and notes, not whether we fact-check)
    is_state = is_state_media(source_name)
    
    # Fact-check claims for all sources (not just state media) so status can be verified when corroborated
    fact_check_notes = []
    verified_count = 0
    propaganda_count = 0
    
    for claim in claims[:5]:  # Limit to 5 claims
        result = await tavily_client.fact_check_claim(
            claim=claim,
            source_type=state.get("source_type", "telegram")
        )
        
        status = result.get("status", "unverified")
        notes = result.get("notes", [])
        
        fact_check_notes.extend(notes)
        
        if status == "verified":
            verified_count += 1
        elif status == "propaganda":
            propaganda_count += 1
    
    # Determine overall status from fact-check results (same logic for all sources)
    if verified_count >= 2:
        state["fact_check_status"] = "verified"
        if not is_state:
            fact_check_notes.append("Corroborated by trusted outlets; source is not state media.")
    elif propaganda_count > verified_count:
        state["fact_check_status"] = "propaganda"
    elif verified_count == 1:
        state["fact_check_status"] = "unverified"
        fact_check_notes.append("Single corroborating source; additional verification recommended.")
    else:
        state["fact_check_status"] = "unverified"
        if not is_state:
            fact_check_notes.append("Source is not state media; claims require independent verification.")
    
    # Calculate bias score (1-10)
    # Higher score = more state-aligned
    if is_state:
        if state["fact_check_status"] == "propaganda":
            state["bias_score"] = 9
        elif state["fact_check_status"] == "verified":
            state["bias_score"] = 5
        else:
            state["bias_score"] = 7
    else:
        state["bias_score"] = 3
    
    state["fact_check_notes"] = fact_check_notes
    return state
