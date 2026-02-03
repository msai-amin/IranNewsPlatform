#!/usr/bin/env python3
"""Seed the database with sample articles for UI testing."""

import asyncio
import json
import asyncpg
from datetime import datetime, timezone
from pathlib import Path

# Load .env from project root
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv()

from src.config import Config


SAMPLE_ARTICLES = [
    {
        "dedupe_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
        "source_url": "https://example.com/article1",
        "source_name": "VahidOnline",
        "source_type": "telegram",
        "raw_persian_text": "متن نمونه خبر فارسی",
        "english_translation": "Sample Persian news text translation.",
        "fact_check_status": "verified",
        "fact_check_notes": ["Confirmed by Reuters.", "BBC reported similar details."],
        "bias_score": 3,
        "final_copy": "**Iran's President Voices Optimism for Nuclear Deal by Month's End**\n\n**TEHRAN, Iran (AP) —** Iran's president on Wednesday expressed hope for a breakthrough in long-stalled international nuclear negotiations, suggesting a positive result could be achieved by the end of the month, according to remarks made in a public speech.\n\nThe statement by President Ebrahim Raisi offers a rare note of public optimism from Tehran regarding the revival of the landmark 2015 nuclear accord.",
        "processed_at": datetime.now(timezone.utc).replace(tzinfo=None),
    },
    {
        "dedupe_hash": "b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7",
        "source_url": "https://example.com/article2",
        "source_name": "IranWire",
        "source_type": "web",
        "raw_persian_text": "متن خبر دوم",
        "english_translation": "Second article translation.",
        "fact_check_status": "unverified",
        "fact_check_notes": ["Could not independently verify claims."],
        "bias_score": 5,
        "final_copy": "**Protesters Gather in Tehran Amid Economic Turmoil**\n\n**TEHRAN (Reuters) —** Small groups of protesters gathered in central Tehran on Thursday, according to eyewitness accounts and social media posts, as Iran grapples with inflation and currency instability.\n\nReuters could not independently verify the scale or duration of the gatherings.",
        "processed_at": datetime.now(timezone.utc).replace(tzinfo=None),
    },
    {
        "dedupe_hash": "c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8",
        "source_url": "https://example.com/article3",
        "source_name": "Tasnim",
        "source_type": "telegram",
        "raw_persian_text": "خبر از منابع دولتی",
        "english_translation": "News from government sources.",
        "fact_check_status": "propaganda",
        "fact_check_notes": ["State-aligned narrative.", "Claims conflict with independent reporting."],
        "bias_score": 8,
        "final_copy": "**Government Announces Major Infrastructure Initiative**\n\n**TEHRAN —** Iranian officials announced a sweeping new infrastructure plan on Friday, pledging billions in investment and thousands of new jobs.\n\nCritics have questioned the feasibility of the project given current economic constraints.",
        "processed_at": datetime.now(timezone.utc).replace(tzinfo=None),
    },
]


async def seed():
    """Insert sample articles into the database."""
    if not Config.DATABASE_URL:
        print("Error: DATABASE_URL not set in .env")
        sys.exit(1)

    print("Connecting to database...")
    conn = await asyncpg.connect(Config.DATABASE_URL)

    try:
        # Check if table exists
        exists = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='articles')"
        )
        if not exists:
            print("Error: articles table does not exist. Run the API server first to create it.")
            sys.exit(1)

        for i, article in enumerate(SAMPLE_ARTICLES):
            try:
                await conn.execute(
                    """
                    INSERT INTO articles (
                        dedupe_hash, source_url, source_name, source_type,
                        raw_persian_text, english_translation, fact_check_status,
                        fact_check_notes, bias_score, final_copy, processed_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (dedupe_hash) DO NOTHING
                    """,
                    article["dedupe_hash"],
                    article["source_url"],
                    article["source_name"],
                    article["source_type"],
                    article["raw_persian_text"],
                    article["english_translation"],
                    article["fact_check_status"],
                    json.dumps(article["fact_check_notes"]) if article["fact_check_notes"] else None,
                    article["bias_score"],
                    article["final_copy"],
                    article["processed_at"],
                )
                print(f"  ✓ Inserted article {i + 1}: {article['source_name']} ({article['fact_check_status']})")
            except Exception as e:
                print(f"  ✗ Skipped article {i + 1}: {e}")

        print("\nDone! Refresh the UI at http://localhost:3000 to see the sample articles.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
