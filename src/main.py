"""Main LangGraph pipeline definition and entry point."""

import asyncio
from datetime import datetime
from typing import Literal, Optional
from langgraph.graph import StateGraph, END
from src.state import NewsState
from src.config import Config
from src.nodes.scout import scout_node
from src.nodes.librarian import librarian_node
from src.nodes.translator import translator_node
from src.nodes.analyst import analyst_node
from src.nodes.editor import editor_node
from src.services.database import DatabaseClient


def _log_for_node(node_name: str, state_update: dict) -> Optional[str]:
    """Generate brief log message for agent log from state update."""
    if node_name == "scout":
        if "is_news" in state_update:
            return f"is_news={state_update['is_news']}"
    if node_name == "librarian":
        if "is_duplicate" in state_update:
            return f"is_duplicate={state_update['is_duplicate']}"
        if "error" in state_update:
            return state_update["error"][:200] if state_update["error"] else None
    if node_name == "analyst":
        if "fact_check_status" in state_update:
            return f"status={state_update['fact_check_status']}"
    return None


def should_continue_after_scout(state: NewsState) -> str:
    """Conditional edge: continue if is_news=True."""
    if state.get("is_news", False):
        return "librarian"
    return "__end__"


def should_continue_after_librarian(state: NewsState) -> str:
    """Conditional edge: continue if not duplicate."""
    if not state.get("is_duplicate", False):
        return "translator"
    return "__end__"


def create_news_graph():
    """Create and compile LangGraph StateGraph."""
    
    # Create graph
    workflow = StateGraph(NewsState)
    
    # Add nodes
    workflow.add_node("scout", scout_node)
    workflow.add_node("librarian", librarian_node)
    workflow.add_node("translator", translator_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("editor", editor_node)
    
    # Set entry point
    workflow.set_entry_point("scout")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "scout",
        should_continue_after_scout,
        {
            "librarian": "librarian",
            "__end__": END
        }
    )
    
    workflow.add_conditional_edges(
        "librarian",
        should_continue_after_librarian,
        {
            "translator": "translator",
            "__end__": END
        }
    )
    
    # Linear flow after librarian
    workflow.add_edge("translator", "analyst")
    workflow.add_edge("analyst", "editor")
    workflow.add_edge("editor", END)
    
    # Compile graph (checkpointing disabled for now - PostgresSaver needs async context)
    app = workflow.compile()
    return app


async def process_news_item(state: NewsState) -> NewsState:
    """Process a single news item through the pipeline.
    
    Args:
        state: Initial state with raw_persian_text
        
    Returns:
        Final state with processed article
    """
    app = create_news_graph()
    
    # Generate thread ID from source URL or use default
    thread_id = state.get("source_url", "default").replace("/", "_").replace(":", "_")
    config = {"configurable": {"thread_id": thread_id}}
    
    run_id = state.get("run_id")
    db_client = None
    if run_id:
        db_client = DatabaseClient()
        await db_client.connect()
    
    # Use astream to record per-node events for agent log
    final_state = dict(state)
    
    try:
        async for chunk in app.astream(state, config):
            for node_name, state_update in chunk.items():
                completed_at = datetime.utcnow()
                
                # Merge update into final state
                if isinstance(state_update, dict):
                    for k, v in state_update.items():
                        if v is not None:
                            final_state[k] = v
                    
                    # Record node event for agent log
                    if run_id and db_client and db_client.conn_pool:
                        log_msg = _log_for_node(node_name, state_update)
                        await db_client.insert_node_event(
                            run_id=run_id,
                            node_name=node_name,
                            completed_at=completed_at,
                            duration_ms=None,
                            status="ok",
                            log_message=log_msg,
                        )
    finally:
        if db_client:
            await db_client.close()
    
    # Save to database (skip if no connection or no final copy)
    if final_state.get("final_copy"):
        try:
            db_client = DatabaseClient()
            await db_client.connect()
            if db_client.conn_pool:
                await db_client.save_article({
                    "dedupe_hash": final_state.get("dedupe_hash", ""),
                    "source_url": final_state.get("source_url", ""),
                    "source_name": final_state.get("source_name", ""),
                    "source_type": final_state.get("source_type", ""),
                    "raw_persian_text": final_state.get("raw_persian_text", ""),
                    "english_translation": final_state.get("english_translation", ""),
                    "fact_check_status": final_state.get("fact_check_status", "unverified"),
                    "fact_check_notes": final_state.get("fact_check_notes", []),
                    "bias_score": final_state.get("bias_score"),
                    "final_copy": final_state.get("final_copy", ""),
                    "story_group_id": final_state.get("story_group_id"),
                    "is_primary": final_state.get("is_primary", True)
                })
                is_corroboration = not final_state.get("is_primary", True)
                corr_label = " (corroboration)" if is_corroboration else ""
                print(f"  → Saved to database: {final_state.get('source_name')}{corr_label}")
            else:
                print("  → Database not connected, article not saved")
            await db_client.close()
        except Exception as e:
            print(f"  → Database save failed: {e}")
    
    return final_state


if __name__ == "__main__":
    # Example usage
    async def main():
        # Longer news-like Persian text (MIN_TEXT_LENGTH=50)
        test_state: NewsState = {
            "source_url": "https://t.me/test/456",
            "source_type": "telegram",
            "source_name": "test_channel",
            "raw_persian_text": "بانک مرکزی ایران امروز نرخ بهره جدید را اعلام کرد. بر اساس اعلام این بانک نرخ سود از هفت درصد به نه درصد افزایش یافته است.",
            "is_news": False,
            "is_duplicate": False,
            "fact_check_status": "pending",
            "fact_check_notes": []
        }
        
        result = await process_news_item(test_state)
        print("Final state:", result)
    
    asyncio.run(main())
