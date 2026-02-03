# Iran News Wire

An autonomous, resilient, and cost-efficient news gathering engine for Iran. This system uses a tiered AI model strategy to process Persian news from Telegram channels and web sources, translating, fact-checking, and generating AP Style news articles.

## Architecture

The system uses **LangGraph** for orchestration with a 5-node pipeline:

1. **Scout** (gemini-2.5-flash-lite) - Filters and classifies content as news
2. **Librarian** - Deduplicates using MD5 hashing and Pinecone vector similarity
3. **Translator** (gemini-3-flash) - Literal Persian-English translation preserving tone
4. **Analyst** (gemini-3-flash + Tavily) - Fact-checks claims against trusted sources
5. **Editor** (gemini-3-pro/claude-3-5-sonnet) - Generates AP Style news copy

## Features

- **Cost-Efficient**: Tiered model strategy uses cheap models for filtering/translation, expensive models only for final editing
- **Resilient**: Automatic Telegram session rotation on FloodWait errors
- **Deduplication**: MD5 hash + vector similarity prevents duplicate articles
- **Fact-Checking**: Cross-references state media claims with trusted international sources
- **Persian-Aware**: Handles drop-pronouns and preserves original tone/bias

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL (or Supabase)
- Redis (for session management)
- API Keys:
  - Google AI (Gemini)
  - Pinecone
  - Tavily
  - Telegram (API ID/Hash)
  - Firecrawl
  - OpenAI (for embeddings)
  - Optional: Anthropic (Claude)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/msai-amin/IranNewsPlatform.git
cd IranNewsPlatform
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Set up Telegram sessions:
   - Get Telegram API credentials from https://my.telegram.org
   - Generate session strings using Telethon
   - Add comma-separated session strings to `TELEGRAM_SESSION_STRINGS` in `.env`

5. Configure channels in `src/runner.py`:
```python
TELEGRAM_CHANNELS = ["channel1", "channel2", ...]
```

### Running

**Local Development:**
```bash
python -m src.runner
```

**Docker:**
```bash
cd docker
docker-compose up -d
```

## Configuration

Key configuration options in `.env`:

- `MODEL_EDITOR`: Choose `gemini-3-pro` or `claude-3-5-sonnet` for final editing
- `DEDUPE_SIMILARITY_THRESHOLD`: Vector similarity threshold (default: 0.95)
- `DEDUPE_TIME_WINDOW_HOURS`: Time window for duplicate checking (default: 24)
- `IRAN_PROXIES`: Comma-separated proxy list for .ir domains
- `GLOBAL_PROXIES`: Comma-separated proxy list for international domains

## Project Structure

```
src/
├── main.py              # LangGraph pipeline definition
├── state.py             # NewsState TypedDict
├── config.py            # Configuration management
├── runner.py            # Main entry point
├── nodes/               # LangGraph nodes
│   ├── scout.py
│   ├── librarian.py
│   ├── translator.py
│   ├── analyst.py
│   └── editor.py
├── ingestion/           # Data ingestion
│   ├── telegram_listener.py
│   ├── web_scraper.py
│   └── session_manager.py
├── services/            # External services
│   ├── llm.py
│   ├── embeddings.py
│   ├── pinecone_client.py
│   ├── tavily_client.py
│   ├── database.py
│   └── proxy_manager.py
└── utils/               # Utilities
    ├── hashing.py
    └── persian.py
```

## License

MIT
