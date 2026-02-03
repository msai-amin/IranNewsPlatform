#!/usr/bin/env python3
"""Fetch recent messages from Telegram channels and process them."""

import asyncio
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from telethon import TelegramClient
from telethon.sessions import StringSession
from src.config import Config
from src.main import process_news_item
from src.services.database import DatabaseClient
from src.state import NewsState


async def fetch_and_process():
    """Fetch recent messages and process them through the pipeline."""
    
    if not Config.TELEGRAM_SESSION_STRINGS:
        print("Error: TELEGRAM_SESSION_STRINGS not set in .env")
        return
    
    session_string = Config.TELEGRAM_SESSION_STRINGS[0]
    
    # Connect to Telegram
    print("Connecting to Telegram...")
    client = TelegramClient(
        StringSession(session_string),
        int(Config.TELEGRAM_API_ID),
        Config.TELEGRAM_API_HASH
    )
    await client.start()
    print("Connected!\n")
    
    # Channels to fetch from
    channels = [
        "VahidOnline",
        "mamlekate", 
        "Tasvir_1500",
        "bbcpersian",
        "radiofarda_official",
        "IranintlTV",
        "factnameh",
        "HengawO",
        "presstv",
    ]
    
    # Number of recent messages to fetch per channel
    limit = 5
    
    processed = 0
    
    for channel_name in channels:
        print(f"Fetching from @{channel_name}...")
        try:
            entity = await client.get_entity(channel_name)
            messages = await client.get_messages(entity, limit=limit)
            
            for msg in messages:
                if not msg.message or len(msg.message) < 50:
                    continue
                
                print(f"\n--- Processing message from {channel_name} ---")
                print(f"Preview: {msg.message[:100]}...")
                
                run_id = str(uuid.uuid4())
                # Create initial state
                state: NewsState = {
                    "source_url": f"https://t.me/{channel_name}/{msg.id}",
                    "source_type": "telegram",
                    "source_name": channel_name,
                    "raw_persian_text": msg.message,
                    "is_news": False,
                    "is_duplicate": False,
                    "fact_check_status": "pending",
                    "fact_check_notes": [],
                    "run_id": run_id,
                }
                started_at = datetime.utcnow()
                db_client = DatabaseClient()
                await db_client.connect()
                if db_client.conn_pool:
                    await db_client.insert_pipeline_run(
                        run_id=run_id,
                        source_name=channel_name,
                        source_url=state["source_url"],
                    )
                
                try:
                    # Process through pipeline
                    result = await process_news_item(state)
                    completed_at = datetime.utcnow()
                    duration_ms = int((completed_at - started_at).total_seconds() * 1000)
                    
                    if result.get("final_copy"):
                        status = "completed"
                        outcome = "saved"
                        error_message = None
                        print(f"✓ Processed: {result.get('fact_check_status')}")
                        processed += 1
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
                        print(f"✗ Filtered: {reason}")
                    
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
                    print(f"✗ Error: {e}")
                finally:
                    await db_client.close()
                    
        except Exception as e:
            print(f"✗ Could not fetch from {channel_name}: {e}")
    
    await client.disconnect()
    print(f"\n{'='*50}")
    print(f"Done! Processed {processed} articles.")
    print("Refresh the UI to see new articles.")


if __name__ == "__main__":
    asyncio.run(fetch_and_process())
