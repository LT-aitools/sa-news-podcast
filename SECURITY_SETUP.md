# Security Setup Instructions

## Overview
This document explains how to set up secure API key storage for the SA News Podcast project, following the security requirements in AGENTS.md.

## Required Setup

### 1. Create Secrets File
You need to create a `secrets.json` file in `~/.config/sa-podcast/` with your API keys.

**Location:** `~/.config/sa-podcast/secrets.json`

### 2. Copy Template
A template file has been created at `~/.config/sa-podcast/secrets.json.template`. Copy this file and fill in your actual API keys:

```bash
cp ~/.config/sa-podcast/secrets.json.template ~/.config/sa-podcast/secrets.json
```

### 3. Fill in Your API Keys
Edit `~/.config/sa-podcast/secrets.json` and replace the placeholder values with your actual API keys:

```json
{
  "azure_speech": {
    "subscription_key": "your_actual_azure_speech_key",
    "region": "your_azure_region"
  },
  "claude": {
    "api_key": "your_actual_claude_api_key"
  },
  "openai": {
    "api_key": "your_actual_openai_api_key"
  },
  "perplexity": {
    "api_key": "your_actual_perplexity_api_key"
  },
  "cleanup": {
    "secret_key": "your_cleanup_secret_key"
  }
}
```

### 4. Set Proper Permissions
Make sure the secrets file is only readable by you:

```bash
chmod 600 ~/.config/sa-podcast/secrets.json
```

## API Keys Explained

### Required for AI Workflow:
- **Azure Speech**: For text-to-speech conversion (Leah voice)
- **Claude**: For generating podcast transcripts from news
- **OpenAI**: For fetching news content (GPT-5 with web search)
- **Perplexity**: For fetching news content (Sonar with web search)

### Optional:
- **Cleanup Secret Key**: Security key for the cleanup API endpoint that automatically deletes old podcast episodes (older than 30 days). This prevents your storage from filling up with old episodes. You can set this to any random string like "my-secret-cleanup-key-123".

## Security Benefits

✅ **No secrets in project folder** - All API keys are stored outside the project directory  
✅ **File-based secrets** - More secure than environment variables  
✅ **Git-safe** - Secrets are never committed to version control  
✅ **Proper permissions** - File is only readable by the owner  

## What Changed

The following files have been updated to use secure secret storage:

- `podcast_creator.py` - Azure Speech API credentials
- `ai_news_fetcher.py` - Claude, OpenAI, and Perplexity API credentials
- `transcript_generator.py` - Claude API credentials
- `scripts/speechsynthesis.py` - Azure Speech API credentials
- `api/cleanup-old-episodes.js` - Cleanup secret key
- `secure_secrets.py` - New secure secrets loader module
- `.gitignore` - Updated to prevent secret file commits
- `requirements.txt` - Updated with new AI API dependencies

### Removed (No Longer Needed):
- Email credentials (replaced by AI news fetching)
- Google API key (replaced by Claude for transcript generation)

## Testing

After setting up your secrets file, you can test that everything works by running:

```bash
python3 -c "from secure_secrets import get_secrets; print('Secrets loaded successfully')"
```

## Troubleshooting

If you get errors about missing secrets:

1. Check that `~/.config/sa-podcast/secrets.json` exists
2. Verify the JSON format is valid
3. Ensure all required API keys are filled in
4. Check file permissions with `ls -la ~/.config/sa-podcast/secrets.json`

The file should show permissions like `-rw-------` (only readable by owner).
