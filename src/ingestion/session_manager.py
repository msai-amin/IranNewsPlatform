"""Telegram session manager with rotation for FloodWait handling."""

import asyncio
from typing import Optional
from telethon.errors import FloodWaitError
from telethon import TelegramClient
from telethon.sessions import StringSession
from src.config import Config

try:
    import redis.asyncio as redis
except ImportError:
    redis = None


class SessionManager:
    """Manages multiple Telegram sessions with automatic rotation."""
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions: list[TelegramClient] = []
        self.current_index = 0
        self.redis_client: Optional[object] = None
        self.rate_limit_cooldowns: dict[int, float] = {}  # session_index -> unblock_time
    
    async def initialize(self):
        """Initialize all Telegram sessions."""
        if Config.REDIS_URL and redis:
            try:
                self.redis_client = await redis.from_url(Config.REDIS_URL)
            except Exception as e:
                print(f"Redis connection error: {e}")
        
        # Initialize sessions from environment
        for i, session_string in enumerate(Config.TELEGRAM_SESSION_STRINGS):
            if not session_string.strip():
                continue
            
            try:
                # Use StringSession for session strings
                session = StringSession(session_string.strip())
                client = TelegramClient(
                    session,
                    int(Config.TELEGRAM_API_ID),
                    Config.TELEGRAM_API_HASH
                )
                await client.start()
                self.sessions.append(client)
                print(f"Initialized Telegram session {i}")
            except Exception as e:
                print(f"Failed to initialize session {i}: {e}")
        
        if not self.sessions:
            raise ValueError("No valid Telegram sessions available")
    
    async def get_active_client(self) -> TelegramClient:
        """Get an active client, rotating if needed.
        
        Returns:
            Active TelegramClient
        """
        import time
        
        # Find next available session
        attempts = 0
        while attempts < len(self.sessions):
            idx = self.current_index % len(self.sessions)
            client = self.sessions[idx]
            
            # Check if session is rate-limited
            cooldown = self.rate_limit_cooldowns.get(idx, 0)
            if time.time() < cooldown:
                self.current_index += 1
                attempts += 1
                continue
            
            return client
        
        # All sessions rate-limited, wait for shortest cooldown
        if self.rate_limit_cooldowns:
            min_cooldown = min(self.rate_limit_cooldowns.values())
            wait_time = max(0, min_cooldown - time.time())
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        return self.sessions[0]
    
    async def handle_flood_wait(self, error: FloodWaitError, session_index: int):
        """Handle FloodWaitError by updating cooldown.
        
        Args:
            error: FloodWaitError exception
            session_index: Index of rate-limited session
        """
        import time
        wait_seconds = error.seconds
        unblock_time = time.time() + wait_seconds + 10  # Add buffer
        
        self.rate_limit_cooldowns[session_index] = unblock_time
        
        # Store in Redis if available
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    f"telegram_cooldown_{session_index}",
                    wait_seconds + 10,
                    str(unblock_time)
                )
            except Exception as e:
                print(f"Redis error: {e}")
        
        # Rotate to next session
        self.current_index += 1
        print(f"Session {session_index} rate-limited for {wait_seconds}s, rotating...")
    
    async def close_all(self):
        """Close all sessions."""
        for client in self.sessions:
            try:
                await client.disconnect()
            except Exception:
                pass
        
        if self.redis_client:
            await self.redis_client.close()
