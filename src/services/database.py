"""PostgreSQL database client for state checkpointing and deduplication."""

import asyncpg
from typing import Optional
from datetime import datetime
from src.config import Config


class DatabaseClient:
    """PostgreSQL client for article storage and deduplication."""
    
    def __init__(self):
        """Initialize database connection pool."""
        self.conn_pool: Optional[asyncpg.Pool] = None
        self.database_url = Config.DATABASE_URL
    
    async def connect(self):
        """Create connection pool."""
        if not self.database_url:
            print("Warning: DATABASE_URL not set, database operations will be skipped")
            return
        
        try:
            self.conn_pool = await asyncpg.create_pool(self.database_url)
            await self._create_tables()
        except Exception as e:
            print(f"Database connection error: {e}")
    
    async def close(self):
        """Close connection pool."""
        if self.conn_pool:
            await self.conn_pool.close()
    
    async def _create_tables(self):
        """Create required tables if they don't exist."""
        if not self.conn_pool:
            return
        
        async with self.conn_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id SERIAL PRIMARY KEY,
                    dedupe_hash VARCHAR(32) UNIQUE NOT NULL,
                    source_url TEXT,
                    source_name VARCHAR(255),
                    source_type VARCHAR(20),
                    raw_persian_text TEXT,
                    english_translation TEXT,
                    fact_check_status VARCHAR(20),
                    fact_check_notes JSONB,
                    bias_score INTEGER,
                    final_copy TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    processed_at TIMESTAMP,
                    story_group_id UUID,
                    is_primary BOOLEAN DEFAULT true
                );
                
                CREATE INDEX IF NOT EXISTS idx_dedupe_hash ON articles(dedupe_hash);
                CREATE INDEX IF NOT EXISTS idx_created_at ON articles(created_at);
                CREATE INDEX IF NOT EXISTS idx_fact_check_status ON articles(fact_check_status);
                CREATE INDEX IF NOT EXISTS idx_story_group_id ON articles(story_group_id);
            """)
            
            # Add columns if they don't exist (for existing databases)
            await conn.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='articles' AND column_name='bias_score') THEN
                        ALTER TABLE articles ADD COLUMN bias_score INTEGER;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='articles' AND column_name='fact_check_notes') THEN
                        ALTER TABLE articles ADD COLUMN fact_check_notes JSONB;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='articles' AND column_name='story_group_id') THEN
                        ALTER TABLE articles ADD COLUMN story_group_id UUID;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='articles' AND column_name='is_primary') THEN
                        ALTER TABLE articles ADD COLUMN is_primary BOOLEAN DEFAULT true;
                    END IF;
                END $$;
            """)
            
            # Create index for story_group_id if not exists
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_story_group_id ON articles(story_group_id);
            """)
            
            # Pipeline runs table for dev dashboard
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_runs (
                    id SERIAL PRIMARY KEY,
                    run_id UUID UNIQUE NOT NULL,
                    source_name VARCHAR(255),
                    source_url TEXT,
                    status VARCHAR(20) NOT NULL,
                    outcome VARCHAR(30),
                    error_message TEXT,
                    started_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP,
                    duration_ms INTEGER
                );
                CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at ON pipeline_runs(started_at DESC);
                CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);
            """)
            
            # Pipeline node events for agent log
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_node_events (
                    id SERIAL PRIMARY KEY,
                    run_id UUID NOT NULL,
                    node_name VARCHAR(50) NOT NULL,
                    started_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP,
                    duration_ms INTEGER,
                    status VARCHAR(20) DEFAULT 'ok',
                    log_message TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_node_events_run_id ON pipeline_node_events(run_id);
                CREATE INDEX IF NOT EXISTS idx_node_events_started_at ON pipeline_node_events(started_at DESC);
            """)
    
    async def check_hash_exists(self, dedupe_hash: str) -> bool:
        """Check if article hash already exists.
        
        Args:
            dedupe_hash: MD5 hash of article
            
        Returns:
            True if hash exists
        """
        if not self.conn_pool:
            return False
        
        try:
            async with self.conn_pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT 1 FROM articles WHERE dedupe_hash = $1 LIMIT 1",
                    dedupe_hash
                )
                return result is not None
        except Exception as e:
            print(f"Database query error: {e}")
            return False
    
    async def save_article(self, article_data: dict):
        """Save processed article to database.
        
        Args:
            article_data: Article data dict
        """
        if not self.conn_pool:
            return
        
        try:
            import json
            import uuid
            fact_check_notes = article_data.get("fact_check_notes")
            # Convert list to JSON for JSONB column
            fact_check_notes_json = json.dumps(fact_check_notes) if fact_check_notes else None
            
            # Handle story_group_id - generate new UUID if not provided (new story)
            story_group_id = article_data.get("story_group_id")
            if story_group_id is None:
                story_group_id = uuid.uuid4()
            elif isinstance(story_group_id, str):
                story_group_id = uuid.UUID(story_group_id)
            
            is_primary = article_data.get("is_primary", True)
            
            async with self.conn_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO articles (
                        dedupe_hash, source_url, source_name, source_type,
                        raw_persian_text, english_translation, fact_check_status,
                        fact_check_notes, bias_score, final_copy, processed_at,
                        story_group_id, is_primary
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    ON CONFLICT (dedupe_hash) DO NOTHING
                """,
                    article_data.get("dedupe_hash"),
                    article_data.get("source_url"),
                    article_data.get("source_name"),
                    article_data.get("source_type"),
                    article_data.get("raw_persian_text"),
                    article_data.get("english_translation"),
                    article_data.get("fact_check_status"),
                    fact_check_notes_json,
                    article_data.get("bias_score"),
                    article_data.get("final_copy"),
                    datetime.utcnow(),
                    story_group_id,
                    is_primary
                )
        except Exception as e:
            print(f"Database save error: {e}")
    
    async def get_article_by_dedupe_hash(self, dedupe_hash: str) -> dict:
        """Get article by dedupe hash.
        
        Args:
            dedupe_hash: MD5 hash of article
            
        Returns:
            Article data dict or None
        """
        if not self.conn_pool:
            return None
        
        try:
            async with self.conn_pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT id, story_group_id FROM articles WHERE dedupe_hash = $1",
                    dedupe_hash
                )
                if row:
                    return {
                        "id": row["id"],
                        "story_group_id": str(row["story_group_id"]) if row["story_group_id"] else None
                    }
                return None
        except Exception as e:
            print(f"Database query error: {e}")
            return None
    
    async def insert_pipeline_run(
        self,
        run_id: str,
        source_name: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> bool:
        """Insert a pipeline run with status=running.
        
        Args:
            run_id: UUID string for the run
            source_name: Telegram channel or source name
            source_url: Message/source URL
            
        Returns:
            True if inserted
        """
        if not self.conn_pool:
            return False
        try:
            import uuid
            uid = uuid.UUID(run_id)
            async with self.conn_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO pipeline_runs (run_id, source_name, source_url, status)
                    VALUES ($1, $2, $3, 'running')
                """, uid, source_name, source_url)
            return True
        except Exception as e:
            print(f"Pipeline run insert error: {e}")
            return False
    
    async def update_pipeline_run(
        self,
        run_id: str,
        status: str,
        outcome: Optional[str] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
    ) -> bool:
        """Update a pipeline run after completion.
        
        Args:
            run_id: UUID string for the run
            status: completed, filtered, or error
            outcome: saved, duplicate, not_news, or error
            error_message: If status/outcome is error
            completed_at: When pipeline finished
            duration_ms: Elapsed milliseconds
            
        Returns:
            True if updated
        """
        if not self.conn_pool:
            return False
        try:
            import uuid
            uid = uuid.UUID(run_id)
            async with self.conn_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE pipeline_runs
                    SET status = $2, outcome = $3, error_message = $4,
                        completed_at = $5, duration_ms = $6
                    WHERE run_id = $1
                """, uid, status, outcome, error_message, completed_at, duration_ms)
            return True
        except Exception as e:
            print(f"Pipeline run update error: {e}")
            return False
    
    async def insert_node_event(
        self,
        run_id: str,
        node_name: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
        status: str = "ok",
        log_message: Optional[str] = None,
    ) -> bool:
        """Insert a pipeline node event for agent log.
        
        Args:
            run_id: UUID string for the run
            node_name: Name of the node (scout, librarian, translator, analyst, editor)
            started_at: When node started
            completed_at: When node finished
            duration_ms: Node duration in ms
            status: ok, skip, error
            log_message: Brief log (e.g. is_news=False, is_duplicate=True)
            
        Returns:
            True if inserted
        """
        if not self.conn_pool:
            return False
        try:
            import uuid
            uid = uuid.UUID(run_id)
            async with self.conn_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO pipeline_node_events (run_id, node_name, started_at, completed_at, duration_ms, status, log_message)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, uid, node_name, started_at, completed_at, duration_ms, status, log_message or "")
            return True
        except Exception as e:
            print(f"Node event insert error: {e}")
            return False