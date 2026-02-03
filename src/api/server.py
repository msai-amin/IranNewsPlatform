"""FastAPI server for Iran News Wire frontend."""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import asyncpg
import json

from src.config import Config

app = FastAPI(
    title="Iran News Wire API",
    description="API for accessing processed news articles",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database pool
db_pool: Optional[asyncpg.Pool] = None


class CorroboratingSource(BaseModel):
    """A source that corroborates the story."""
    id: int
    source_name: Optional[str]
    source_url: Optional[str]
    processed_at: Optional[datetime]


class Article(BaseModel):
    """Article response model."""
    id: int
    dedupe_hash: str
    source_url: Optional[str]
    source_name: Optional[str]
    source_type: Optional[str]
    raw_persian_text: Optional[str]
    english_translation: Optional[str]
    fact_check_status: Optional[str]
    fact_check_notes: Optional[List[str]]
    bias_score: Optional[int]
    final_copy: Optional[str]
    created_at: Optional[datetime]
    processed_at: Optional[datetime]
    # Corroboration fields
    story_group_id: Optional[str]
    is_primary: Optional[bool]
    corroboration_count: Optional[int] = 1
    corroborating_sources: Optional[List[str]] = []


class ArticleListResponse(BaseModel):
    """Paginated article list response."""
    articles: List[Article]
    total: int
    page: int
    limit: int
    total_pages: int


class StatsResponse(BaseModel):
    """Dashboard statistics response."""
    total: int
    verified: int
    unverified: int
    propaganda: int
    pending: int
    by_source_type: dict


class PipelineRun(BaseModel):
    """Single pipeline run for dev dashboard."""
    run_id: str
    source_name: Optional[str]
    source_url: Optional[str]
    status: str
    outcome: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]


class PipelineRunsResponse(BaseModel):
    """List of pipeline runs."""
    runs: List[PipelineRun]


class PipelineStatsResponse(BaseModel):
    """Aggregate pipeline stats for dev dashboard."""
    total_runs: int
    by_status: dict
    by_outcome: dict
    last_run_at: Optional[datetime]


class PipelineNodeEvent(BaseModel):
    """Single node event for agent log."""
    id: int
    run_id: str
    node_name: str
    completed_at: Optional[datetime]
    status: str
    log_message: Optional[str]
    source_name: Optional[str] = None


class PipelineAgentsResponse(BaseModel):
    """List of pipeline node events (agent log)."""
    events: List[PipelineNodeEvent]


async def _ensure_tables():
    """Create articles table if it doesn't exist and add new columns for existing tables."""
    if not db_pool:
        return
    async with db_pool.acquire() as conn:
        # Step 1: Create base table if it doesn't exist (without new columns to avoid issues)
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
                processed_at TIMESTAMP
            );
        """)
        
        # Step 2: Add columns if they don't exist (for existing databases)
        await conn.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='articles' AND column_name='bias_score') THEN
                    ALTER TABLE articles ADD COLUMN bias_score INTEGER;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='articles' AND column_name='fact_check_notes') THEN
                    ALTER TABLE articles ADD COLUMN fact_check_notes JSONB;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='articles' AND column_name='story_group_id') THEN
                    ALTER TABLE articles ADD COLUMN story_group_id UUID;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='articles' AND column_name='is_primary') THEN
                    ALTER TABLE articles ADD COLUMN is_primary BOOLEAN DEFAULT true;
                END IF;
            END $$;
        """)
        
        # Step 3: Create indexes after columns exist
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_dedupe_hash ON articles(dedupe_hash);
            CREATE INDEX IF NOT EXISTS idx_created_at ON articles(created_at);
            CREATE INDEX IF NOT EXISTS idx_fact_check_status ON articles(fact_check_status);
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
            CREATE INDEX IF NOT EXISTS idx_node_events_started_at ON pipeline_node_events(completed_at DESC NULLS LAST);
        """)


@app.on_event("startup")
async def startup():
    """Initialize database connection pool."""
    global db_pool
    if Config.DATABASE_URL:
        try:
            db_pool = await asyncpg.create_pool(Config.DATABASE_URL)
            await _ensure_tables()
            print("Database connected")
        except Exception as e:
            print(f"Database connection error: {e}")


@app.on_event("shutdown")
async def shutdown():
    """Close database connection pool."""
    global db_pool
    if db_pool:
        await db_pool.close()


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "database": db_pool is not None}


@app.get("/api/articles", response_model=ArticleListResponse)
async def list_articles(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by fact_check_status"),
    source_type: Optional[str] = Query(None, description="Filter by source_type (telegram/web)"),
    search: Optional[str] = Query(None, description="Search in final_copy"),
):
    """List articles with pagination and filtering.
    
    Only returns primary articles (is_primary=true), with corroboration count.
    """
    if not db_pool:
        return ArticleListResponse(
            articles=[],
            total=0,
            page=page,
            limit=limit,
            total_pages=1,
        )
    
    offset = (page - 1) * limit
    
    # Build query with filters - only show primary articles
    conditions = ["(is_primary = true OR is_primary IS NULL)"]
    params = []
    param_idx = 1
    
    if status:
        conditions.append(f"fact_check_status = ${param_idx}")
        params.append(status)
        param_idx += 1
    
    if source_type:
        conditions.append(f"source_type = ${param_idx}")
        params.append(source_type)
        param_idx += 1
    
    if search:
        conditions.append(f"final_copy ILIKE ${param_idx}")
        params.append(f"%{search}%")
        param_idx += 1
    
    where_clause = f"WHERE {' AND '.join(conditions)}"
    
    async with db_pool.acquire() as conn:
        # Get total count of primary articles
        count_query = f"SELECT COUNT(*) FROM articles {where_clause}"
        total = await conn.fetchval(count_query, *params)
        
        # Get articles with corroboration count
        query = f"""
            SELECT a.id, a.dedupe_hash, a.source_url, a.source_name, a.source_type,
                   a.raw_persian_text, a.english_translation, a.fact_check_status,
                   a.fact_check_notes, a.bias_score, a.final_copy, a.created_at, 
                   a.processed_at, a.story_group_id, a.is_primary,
                   (SELECT COUNT(*) FROM articles a2 
                    WHERE a2.story_group_id = a.story_group_id 
                    AND a.story_group_id IS NOT NULL) as corroboration_count,
                   (SELECT array_agg(DISTINCT a3.source_name) FROM articles a3 
                    WHERE a3.story_group_id = a.story_group_id 
                    AND a3.id != a.id
                    AND a.story_group_id IS NOT NULL) as corroborating_sources
            FROM articles a
            {where_clause}
            ORDER BY a.processed_at DESC NULLS LAST, a.created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, offset])
        rows = await conn.fetch(query, *params)
        
        articles = []
        for row in rows:
            # Parse fact_check_notes - may be JSON string or already a list
            notes = row["fact_check_notes"]
            if isinstance(notes, str):
                try:
                    notes = json.loads(notes)
                except json.JSONDecodeError:
                    notes = None
            
            # Parse corroborating_sources - may be array or None
            corroborating = row["corroborating_sources"]
            if corroborating is None:
                corroborating = []
            
            # Corroboration count defaults to 1 (the article itself)
            corr_count = row["corroboration_count"] or 1
            
            article = Article(
                id=row["id"],
                dedupe_hash=row["dedupe_hash"],
                source_url=row["source_url"],
                source_name=row["source_name"],
                source_type=row["source_type"],
                raw_persian_text=row["raw_persian_text"],
                english_translation=row["english_translation"],
                fact_check_status=row["fact_check_status"],
                fact_check_notes=notes,
                bias_score=row["bias_score"],
                final_copy=row["final_copy"],
                created_at=row["created_at"],
                processed_at=row["processed_at"],
                story_group_id=str(row["story_group_id"]) if row["story_group_id"] else None,
                is_primary=row["is_primary"],
                corroboration_count=corr_count,
                corroborating_sources=corroborating,
            )
            articles.append(article)
        
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        
        return ArticleListResponse(
            articles=articles,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )


@app.get("/api/articles/{article_id}", response_model=Article)
async def get_article(article_id: int):
    """Get a single article by ID with corroboration data."""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT a.id, a.dedupe_hash, a.source_url, a.source_name, a.source_type,
                   a.raw_persian_text, a.english_translation, a.fact_check_status,
                   a.fact_check_notes, a.bias_score, a.final_copy, a.created_at, 
                   a.processed_at, a.story_group_id, a.is_primary,
                   (SELECT COUNT(*) FROM articles a2 
                    WHERE a2.story_group_id = a.story_group_id 
                    AND a.story_group_id IS NOT NULL) as corroboration_count,
                   (SELECT array_agg(DISTINCT a3.source_name) FROM articles a3 
                    WHERE a3.story_group_id = a.story_group_id 
                    AND a3.id != a.id
                    AND a.story_group_id IS NOT NULL) as corroborating_sources
            FROM articles a
            WHERE a.id = $1
            """,
            article_id
        )
        
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Parse fact_check_notes - may be JSON string or already a list
        notes = row["fact_check_notes"]
        if isinstance(notes, str):
            try:
                notes = json.loads(notes)
            except json.JSONDecodeError:
                notes = None
        
        # Parse corroborating_sources
        corroborating = row["corroborating_sources"]
        if corroborating is None:
            corroborating = []
        
        corr_count = row["corroboration_count"] or 1
        
        return Article(
            id=row["id"],
            dedupe_hash=row["dedupe_hash"],
            source_url=row["source_url"],
            source_name=row["source_name"],
            source_type=row["source_type"],
            raw_persian_text=row["raw_persian_text"],
            english_translation=row["english_translation"],
            fact_check_status=row["fact_check_status"],
            fact_check_notes=notes,
            bias_score=row["bias_score"],
            final_copy=row["final_copy"],
            created_at=row["created_at"],
            processed_at=row["processed_at"],
            story_group_id=str(row["story_group_id"]) if row["story_group_id"] else None,
            is_primary=row["is_primary"],
            corroboration_count=corr_count,
            corroborating_sources=corroborating,
        )


@app.get("/api/articles/{article_id}/sources", response_model=List[CorroboratingSource])
async def get_corroborating_sources(article_id: int):
    """Get all sources corroborating a story (articles in the same story group)."""
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    
    async with db_pool.acquire() as conn:
        # First get the story_group_id of the article
        story_group_id = await conn.fetchval(
            "SELECT story_group_id FROM articles WHERE id = $1",
            article_id
        )
        
        if not story_group_id:
            return []
        
        # Get all articles in the same story group
        rows = await conn.fetch(
            """
            SELECT id, source_name, source_url, processed_at
            FROM articles
            WHERE story_group_id = $1
            ORDER BY processed_at DESC NULLS LAST
            """,
            story_group_id
        )
        
        return [
            CorroboratingSource(
                id=row["id"],
                source_name=row["source_name"],
                source_url=row["source_url"],
                processed_at=row["processed_at"]
            )
            for row in rows
        ]


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get dashboard statistics."""
    if not db_pool:
        return StatsResponse(
            total=0,
            verified=0,
            unverified=0,
            propaganda=0,
            pending=0,
            by_source_type={},
        )
    
    async with db_pool.acquire() as conn:
        # Status counts
        status_counts = await conn.fetch(
            """
            SELECT fact_check_status, COUNT(*) as count
            FROM articles
            GROUP BY fact_check_status
            """
        )
        
        # Source type counts
        source_counts = await conn.fetch(
            """
            SELECT source_type, COUNT(*) as count
            FROM articles
            GROUP BY source_type
            """
        )
        
        stats = {
            "total": 0,
            "verified": 0,
            "unverified": 0,
            "propaganda": 0,
            "pending": 0,
        }
        
        for row in status_counts:
            status = row["fact_check_status"] or "pending"
            count = row["count"]
            stats["total"] += count
            if status in stats:
                stats[status] = count
        
        by_source_type = {}
        for row in source_counts:
            source = row["source_type"] or "unknown"
            by_source_type[source] = row["count"]
        
        return StatsResponse(
            total=stats["total"],
            verified=stats["verified"],
            unverified=stats["unverified"],
            propaganda=stats["propaganda"],
            pending=stats["pending"],
            by_source_type=by_source_type,
        )


@app.get("/api/pipeline/runs", response_model=PipelineRunsResponse)
async def get_pipeline_runs(
    limit: int = Query(50, ge=1, le=200, description="Max runs to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """List recent pipeline runs for dev dashboard."""
    if not db_pool:
        return PipelineRunsResponse(runs=[])
    
    conditions = []
    params = []
    param_idx = 1
    if status:
        conditions.append(f"status = ${param_idx}")
        params.append(status)
        param_idx += 1
    params.append(limit)
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    async with db_pool.acquire() as conn:
        query = f"""
            SELECT run_id, source_name, source_url, status, outcome,
                   error_message, started_at, completed_at, duration_ms
            FROM pipeline_runs
            {where_clause}
            ORDER BY started_at DESC
            LIMIT ${param_idx}
        """
        rows = await conn.fetch(query, *params)
        
        runs = [
            PipelineRun(
                run_id=str(row["run_id"]),
                source_name=row["source_name"],
                source_url=row["source_url"],
                status=row["status"],
                outcome=row["outcome"],
                error_message=row["error_message"],
                started_at=row["started_at"],
                completed_at=row["completed_at"],
                duration_ms=row["duration_ms"],
            )
            for row in rows
        ]
        return PipelineRunsResponse(runs=runs)


@app.get("/api/pipeline/stats", response_model=PipelineStatsResponse)
async def get_pipeline_stats():
    """Get aggregate pipeline run stats for dev dashboard."""
    if not db_pool:
        return PipelineStatsResponse(
            total_runs=0,
            by_status={},
            by_outcome={},
            last_run_at=None,
        )
    
    async with db_pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM pipeline_runs")
        
        status_rows = await conn.fetch(
            "SELECT status, COUNT(*) as count FROM pipeline_runs GROUP BY status"
        )
        by_status = {row["status"]: row["count"] for row in status_rows}
        
        outcome_rows = await conn.fetch(
            "SELECT outcome, COUNT(*) as count FROM pipeline_runs WHERE outcome IS NOT NULL GROUP BY outcome"
        )
        by_outcome = {row["outcome"] or "null": row["count"] for row in outcome_rows}
        
        last_row = await conn.fetchrow(
            "SELECT completed_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 1"
        )
        last_run_at = last_row["completed_at"] if last_row and last_row["completed_at"] else (
            await conn.fetchval("SELECT started_at FROM pipeline_runs ORDER BY started_at DESC LIMIT 1")
        )
        
        return PipelineStatsResponse(
            total_runs=total or 0,
            by_status=by_status,
            by_outcome=by_outcome,
            last_run_at=last_run_at,
        )


@app.get("/api/pipeline/agents", response_model=PipelineAgentsResponse)
async def get_pipeline_agents(
    limit: int = Query(100, ge=1, le=500, description="Max events to return"),
    run_id: Optional[str] = Query(None, description="Filter by run_id"),
):
    """Get agent (node) log for dev dashboard."""
    if not db_pool:
        return PipelineAgentsResponse(events=[])
    
    async with db_pool.acquire() as conn:
        if run_id:
            rows = await conn.fetch(
                """
                SELECT e.id, e.run_id, e.node_name, e.completed_at, e.status, e.log_message, r.source_name
                FROM pipeline_node_events e
                LEFT JOIN pipeline_runs r ON r.run_id = e.run_id
                WHERE e.run_id = $1
                ORDER BY e.completed_at ASC NULLS LAST, e.id ASC
                LIMIT $2
                """,
                run_id,
                limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT e.id, e.run_id, e.node_name, e.completed_at, e.status, e.log_message, r.source_name
                FROM pipeline_node_events e
                LEFT JOIN pipeline_runs r ON r.run_id = e.run_id
                ORDER BY e.completed_at DESC NULLS LAST, e.id DESC
                LIMIT $1
                """,
                limit,
            )
        
        events = [
            PipelineNodeEvent(
                id=row["id"],
                run_id=str(row["run_id"]),
                node_name=row["node_name"],
                completed_at=row["completed_at"],
                status=row["status"],
                log_message=row["log_message"],
                source_name=row["source_name"],
            )
            for row in rows
        ]
        return PipelineAgentsResponse(events=events)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
