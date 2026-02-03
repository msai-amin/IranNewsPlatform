#!/usr/bin/env python3
"""Test script to run the Iran News pipeline with sample data."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.main import process_news_item
from src.state import NewsState


async def main():
    """Run pipeline test."""
    # Sample Persian news text (MIN_TEXT_LENGTH=50)
    test_state: NewsState = {
        "source_url": "https://t.me/test/789",
        "source_type": "telegram",
        "source_name": "test_channel",
        "raw_persian_text": "رییس جمهور ایران امروز در سخنرانی خود از پیشرفت مذاکرات هسته‌ای خبر داد. او گفت که امیدوار است تا پایان ماه نتیجه مثبتی حاصل شود.",
        "is_news": False,
        "is_duplicate": False,
        "fact_check_status": "pending",
        "fact_check_notes": [],
    }

    print("Running pipeline test...")
    result = await process_news_item(test_state)

    if result.get("final_copy"):
        print("\n✓ Pipeline completed successfully!")
        print(f"  - is_news: {result.get('is_news')}")
        print(f"  - is_duplicate: {result.get('is_duplicate')}")
        print(f"  - fact_check_status: {result.get('fact_check_status')}")
        print(f"\n--- Final AP Style Copy ---\n{result['final_copy'][:500]}...")
    else:
        print(f"\n✗ Pipeline filtered: {result.get('error', 'Unknown')}")


if __name__ == "__main__":
    asyncio.run(main())
