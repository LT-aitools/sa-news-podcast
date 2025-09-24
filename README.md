# SA News Podcast - Workflow Usage Guide

## Cverview
This project uses AI to create a short (4-5 min) daily mews podcast, focused solely on South African news. It gets automatically created and published every morning SAST. 

## Main steps 
The podcast gets created by: 
1. Get news headlines/digest via LLM-assisted web searches (3 models: Perplexity, OpenAI, Claude). As a fallback, scrape local SA RSS feeds (from Google News, Daily Maverick, and Sunday Times)
2. Feed that info tp Claude, to create a 4-5 min podcast transcript
3. Assemble music & text-to-speech (using Microsoft Azure Text-to-Speech), into a podcast 
4. Publish that podcast in our RSS feed
5. Clean up old (>30 day) episodes, to prevent bloated hosting costs

### Previous versions

The original version of this workflow only used RSS scraping. So now the repo includes two versions: 
1. **AI-Powered Workflow** (New) - Uses AI to fetch news and generate transcripts
2. **RSS Workflow** (Legacy) - Uses existing RSS feeds and Gemini API --> Many of these scripts are in the `/archive` folder.

### Why 3 Models 
In manual testing, we found that the different models (fed the same exact prompt) seemed to preference different types of news, so their digests had almost no overlap in coverage. Assembling a podcast based on the 3 summaries therefore led to the most comprehensive daily news summaries. 

## AI-Powered Workflow (Recommended)

### Quick Start
```bash
# Generate podcast using AI workflow
python podcast_creator.py --ai

# Force regenerate even if episode exists
python podcast_creator.py --ai --force
```

### What It Does
1. **Fetches News** (`scripts/ai_news_fetcher.py`) from 3 AI sources:
   - Perplexity (Sonar)
   - Claude (Sonnet 3.7 with web search)
   - ChatGPT (GPT-5 with web search)

2. **Generates Transcript** (`scripts/transcript_generator.py`) using Claude with:
   - South African timezone dates
   - TTS-optimized formatting
   - Music markers for audio assembly
   - Proper intro/outro structure

3. **Creates Audio** (`podcast_creator.py`) with:
   - Enhanced text sanitization
   - Microsoft TTS with Leah voice
   - Music transitions and assembly
   - MP3 output

### Command Line Options
- `--ai` or `-a`: Use AI-powered workflow
- `--force` or `-f`: Force regenerate even if episode exists
- No flags: Use existing transcript file (RSS workflow)


## File Structure

```
sa-news-podcast/
├── podcast_creator.py          # Main podcast creation script
├── scripts/                    # Active workflow components
│   ├── ai_news_fetcher.py      # AI news fetching system
│   ├── transcript_generator.py # Claude transcript generation
│   ├── secure_secrets.py       # Secure API key management
│   ├── pull_rss_feeds.py       # RSS feeds (backup only)
│   └── README.md               # Scripts documentation
├── archive/                    # Deprecated scripts
│   ├── email_newsletter_retrieval.py # Old email fetching
│   ├── speechsynthesis.py      # Old TTS script
│   ├── generate_podcast_content.py # Old content generation
│   ├── summarize_transcript.py # Old transcript summarization
│   └── README.md               # Archive documentation
├── tests/                      # All test files
│   ├── test_ai_news_fetcher.py
│   ├── test_transcript_generator.py
│   ├── test_text_sanitization.py
│   ├── test_apostrophe_fix.py
│   └── test_workflow_integration.py
├── outputs/                    # Generated content
│   ├── ai_news_digests.txt     # AI news summaries
│   ├── rss_feeds_content.txt   # RSS feeds (backup)
│   └── latest_podcast_summary.txt # Generated transcript
├── public/                     # Final podcast episodes
│   └── YYYY-MM-DD.mp3         # Daily episodes
├── api/                        # API endpoints
│   ├── cleanup-old-episodes.js # Cleanup old episodes
│   └── podcast-feed.js         # RSS feed generation
└── .github/workflows/          # GitHub Actions
    └── daily-podcast.yml       # Automated daily generation
```

## API Keys Required

Set up your API keys in `~/.config/sa-podcast/secrets.json`:

```json
{
  "azure_speech": {
    "subscription_key": "your_azure_speech_key",
    "region": "your_azure_region"
  },
  "claude": {
    "api_key": "your_claude_api_key"
  },
  "openai": {
    "api_key": "your_openai_api_key"
  },
  "perplexity": {
    "api_key": "your_perplexity_api_key"
  }
}
```

## Testing

Run all tests:
```bash
# Run specific test files
python -m pytest tests/test_ai_news_fetcher.py -v
python -m pytest tests/test_transcript_generator.py -v
python -m pytest tests/test_text_sanitization.py -v
python -m pytest tests/test_workflow_integration.py -v

# Run all tests
python -m pytest tests/ -v
```

## Troubleshooting

### Common Issues

1. **"Missing AI modules" error**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`

2. **"Failed to load API keys" error**
   - Check that `~/.config/sa-podcast/secrets.json` exists and has correct API keys

3. **"No transcript was generated" error**
   - Use `--ai` flag to generate new content
   - Check API key validity

4. **Apostrophe pronunciation issues**
   - Fixed automatically with enhanced text sanitization
   - No action needed

### Debug Mode

For detailed logging, check the console output which shows:
- ✅ Successful operations
- ❌ Failed operations  
- ⚠️ Warnings
- 📊 Statistics and validation results

## Code Organization

### Active Scripts (`/scripts/`)
- `ai_news_fetcher.py` - AI news fetching from 3 sources
- `transcript_generator.py` - Claude-based transcript generation
- `secure_secrets.py` - API key management
- `pull_rss_feeds.py` - RSS feeds (backup only)

### Archived Scripts (`/archive/`)
- `email_newsletter_retrieval.py` - Old email newsletter fetching
- `speechsynthesis.py` - Old TTS script
- `generate_podcast_content.py` - Old content generation
- `summarize_transcript.py` - Old transcript summarization

### GitHub Actions (`.github/workflows/`)
- `daily-podcast.yml` - Automated daily generation at 6:00 AM UTC

## Performance

- **AI Workflow**: ~30-60 seconds (depends on API response times)
- **RSS Workflow**: ~10-20 seconds (faster but less current content)
- **Audio Generation**: ~2-5 minutes (depends on transcript length)