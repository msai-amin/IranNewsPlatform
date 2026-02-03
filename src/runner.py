"""Main runner script that ties Telegram listener to LangGraph pipeline."""

import asyncio
import signal
import uuid
from datetime import datetime
from src.main import process_news_item
from src.ingestion.session_manager import SessionManager
from src.ingestion.telegram_listener import TelegramListener
from src.services.database import DatabaseClient
from src.state import NewsState


class NewsWireRunner:
    """Main runner that orchestrates ingestion and processing."""
    
    def __init__(self):
        """Initialize runner."""
        self.session_manager = SessionManager()
        self.telegram_listener = TelegramListener(self.session_manager)
        self.running = False
    
    async def initialize(self):
        """Initialize all components."""
        print("Initializing Iran News Wire...")
        await self.session_manager.initialize()
        self.telegram_listener.set_callback(self._process_message)
        print("Initialization complete.")
    
    async def _process_message(self, state: NewsState):
        """Process incoming message through pipeline.
        
        Args:
            state: Initial state from Telegram
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        db_client = DatabaseClient()
        await db_client.connect()
        
        if db_client.conn_pool:
            await db_client.insert_pipeline_run(
                run_id=run_id,
                source_name=state.get("source_name"),
                source_url=state.get("source_url"),
            )
        
        try:
            text_preview = state.get('raw_persian_text', '')[:50].replace('\n', ' ')
            print(f"\n[{timestamp}] 📨 New message from @{state.get('source_name')}")
            print(f"  Preview: {text_preview}...")
            print(f"  Processing through pipeline...")
            
            state_with_run = {**state, "run_id": run_id}
            result = await process_news_item(state_with_run)
            
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            
            if result.get("final_copy"):
                status = "completed"
                outcome = "saved"
                error_message = None
                print(f"  ✓ Article processed:")
                print(f"    Status: {result.get('fact_check_status')}")
                print(f"    Bias: {result.get('bias_score', 'N/A')}/10")
                headline = result.get('final_copy', '')[:80].split('\n')[0]
                print(f"    Headline: {headline}")
            else:
                status = "filtered"
                reason = result.get("error", "Not news or duplicate")
                error_message = reason
                if "duplicate" in reason.lower() or "hash" in reason.lower():
                    outcome = "duplicate"
                elif "news" in reason.lower() or "is_news" in reason.lower():
                    outcome = "not_news"
                else:
                    outcome = "filtered"
                print(f"  ✗ Filtered: {reason}")
            
            if db_client.conn_pool:
                await db_client.update_pipeline_run(
                    run_id=run_id,
                    status=status,
                    outcome=outcome,
                    error_message=error_message,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                )
        except Exception as e:
            completed_at = datetime.utcnow()
            duration_ms = int((completed_at - started_at).total_seconds() * 1000)
            if db_client.conn_pool:
                await db_client.update_pipeline_run(
                    run_id=run_id,
                    status="error",
                    outcome="error",
                    error_message=str(e),
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                )
            print(f"  ✗ Error: {e}")
        finally:
            await db_client.close()
    
    async def start_telegram_listening(self, channels: list[str]):
        """Start listening to Telegram channels.
        
        Args:
            channels: List of channel usernames
        """
        self.running = True
        await self.telegram_listener.start_listening(channels)
        
        print("\n" + "="*50)
        print("🎧 Listening for new messages...")
        print("   (Pipeline will auto-trigger on new posts)")
        print("   Press Ctrl+C to stop")
        print("="*50 + "\n")
        
        # Keep running until interrupted
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            await self.stop()
    
    async def stop(self):
        """Stop all services."""
        self.running = False
        await self.telegram_listener.stop()
        await self.session_manager.close_all()
        print("Shutdown complete.")


async def main():
    """Main entry point."""
    # Channel list - validated public channels
    # Note: Channels are validated on startup, invalid ones are skipped
    TELEGRAM_CHANNELS = [
        # --- Curation & Citizen Journalism ---
        "VahidOnline",          # Vahid Online
        "mamlekate",            # Mamlekate
        "Tasvir_1500",          # Tasvir 1500
        
        # --- International Persian Media ---
        "bbcpersian",           # BBC Persian
        "radiofarda_official",  # Radio Farda
        "IranintlTV",           # Iran International TV
        
        # --- Fact-Checking ---
        "factnameh",            # Factnameh
        
        # --- Human Rights ---
        "HengawO",              # Hengaw Organization
        
        # --- State Media (for comparison) ---
        "presstv",              # Press TV
    ]
    
    if not TELEGRAM_CHANNELS:
        print("Warning: No Telegram channels configured!")
        print("Edit src/runner.py and add channel usernames to TELEGRAM_CHANNELS")
        return
    
    runner = NewsWireRunner()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        asyncio.create_task(runner.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await runner.initialize()
        await runner.start_telegram_listening(TELEGRAM_CHANNELS)
    except Exception as e:
        print(f"Fatal error: {e}")
        await runner.stop()


if __name__ == "__main__":
    asyncio.run(main())
