"""Telegram listener using Telethon UserBot to scrape channels."""

import asyncio
from typing import Callable, Optional
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, UsernameInvalidError, UsernameNotOccupiedError
from src.ingestion.session_manager import SessionManager
from src.state import NewsState


class TelegramListener:
    """Listens to Telegram channels and feeds messages to pipeline."""
    
    def __init__(self, session_manager: SessionManager):
        """Initialize Telegram listener.
        
        Args:
            session_manager: Session manager for rotation
        """
        self.session_manager = session_manager
        self.callback: Optional[Callable[[NewsState], None]] = None
        self.running = False
        self.valid_channels: list[str] = []
    
    def set_callback(self, callback: Callable[[NewsState], None]):
        """Set callback function to process new messages.
        
        Args:
            callback: Async function that receives NewsState
        """
        self.callback = callback
    
    async def _validate_channels(self, channel_usernames: list[str], client: TelegramClient) -> list[str]:
        """Validate channels by trying to resolve each one.
        
        Args:
            channel_usernames: List of channel usernames to validate
            client: Telegram client to use for validation
            
        Returns:
            List of valid channel usernames
        """
        valid = []
        for username in channel_usernames:
            try:
                entity = await client.get_entity(username)
                valid.append(username)
                print(f"  ✓ {username}")
            except (UsernameInvalidError, UsernameNotOccupiedError, ValueError) as e:
                print(f"  ✗ {username} (invalid or not found)")
            except Exception as e:
                print(f"  ✗ {username} ({type(e).__name__})")
        return valid
    
    async def start_listening(self, channel_usernames: list[str]):
        """Start listening to specified channels.
        
        Args:
            channel_usernames: List of channel usernames (e.g., ['channel1', 'channel2'])
        """
        self.running = True
        
        # First validate channels using the first available session
        if self.session_manager.sessions:
            print("Validating channels...")
            client = self.session_manager.sessions[0]
            self.valid_channels = await self._validate_channels(channel_usernames, client)
            
            if not self.valid_channels:
                print("No valid channels found! Check your channel usernames.")
                return
            
            print(f"\n{len(self.valid_channels)}/{len(channel_usernames)} channels validated")
            print("Channels: " + ", ".join(f"@{c}" for c in self.valid_channels))
        else:
            print("No Telegram sessions available!")
            return
        
        # Register NewMessage on first session only (all sessions would receive same events → duplicate processing)
        client = self.session_manager.sessions[0]

        @client.on(events.NewMessage(chats=self.valid_channels))
        async def handler(event):
            if not self.running:
                return
            try:
                await self._process_message(event, 0)
            except FloodWaitError as e:
                await self.session_manager.handle_flood_wait(e, 0)
            except Exception as e:
                print(f"Error processing message: {e}")

        print(f"Started listening to {len(self.valid_channels)} channels")
    
    async def _process_message(self, event, session_idx: int):
        """Process incoming Telegram message.
        
        Args:
            event: Telethon NewMessage event
            session_idx: Session index
        """
        if not self.callback:
            return
        
        # Extract message data
        message_text = event.message.message or ""
        channel = await event.get_chat()
        channel_name = getattr(channel, 'title', '') or getattr(channel, 'username', '')
        message_link = f"https://t.me/{channel.username}/{event.message.id}" if hasattr(channel, 'username') else ""
        
        # Create initial state
        state: NewsState = {
            "source_url": message_link,
            "source_type": "telegram",
            "source_name": channel_name,
            "raw_persian_text": message_text,
            "is_news": False,
            "is_duplicate": False,
            "fact_check_status": "pending",
            "fact_check_notes": []
        }
        
        # Call pipeline callback
        if self.callback:
            await self.callback(state)
    
    async def stop(self):
        """Stop listening."""
        self.running = False
