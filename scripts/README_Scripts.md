# Scripts - Active Workflow Components

This folder contains the core scripts that power the new AI-driven SA News Podcast workflow.

## 🤖 Active Workflow Scripts

### `ai_news_fetcher.py`
- **Purpose**: Fetches South African news from AI sources
- **Sources**: Perplexity, Claude, ChatGPT
- **Features**: Concurrent API calls, error handling, content validation
- **Output**: Combined news digests file

### `transcript_generator.py`
- **Purpose**: Generates podcast transcripts using Claude
- **Input**: AI news digests + RSS feeds (backup)
- **Features**: Content validation, TTS optimization, length control
- **Output**: Podcast-ready transcript

### `secure_secrets.py`
- **Purpose**: Secure API key management
- **Features**: File-based secrets, environment detection
- **Security**: Keys stored outside project directory
- **Usage**: Loaded by all workflow components

### `pull_rss_feeds.py`
- **Purpose**: RSS feed fetching (backup source)
- **Sources**: Google News, Daily Maverick, Sunday Times
- **Features**: 24-hour filtering, content aggregation
- **Usage**: Only used when 2+ AI sources fail

## 🔄 Workflow Flow

```
1. AI News Fetching (ai_news_fetcher.py)
   ↓
2. Content Validation (count failures)
   ↓
3. RSS Backup (if needed) (pull_rss_feeds.py)
   ↓
4. Transcript Generation (transcript_generator.py)
   ↓
5. Audio Creation (podcast_creator.py)
```

## 🛡️ Security

All scripts use `secure_secrets.py` for API key management:
- Keys stored in `~/.config/sa-podcast/secrets.json`
- No hardcoded credentials
- Environment-aware loading

## 📊 Dependencies

Required packages (see `requirements.txt`):
- `anthropic` - Claude API
- `openai` - Perplexity & ChatGPT APIs  
- `aiohttp` - Async HTTP requests
- `pytz` - Timezone handling
- `requests` - HTTP requests

## 🧪 Testing

All scripts have corresponding test files in `/tests/`:
- `test_ai_news_fetcher.py`
- `test_transcript_generator.py`
- `test_workflow_integration.py`

## 🚀 Usage

Scripts are orchestrated by `podcast_creator.py`:
```bash
python podcast_creator.py --ai
```

Individual components can be tested:
```bash
python scripts/ai_news_fetcher.py
python scripts/transcript_generator.py
```
