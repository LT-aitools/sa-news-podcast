# Secure Setup Guide

This project uses secure secrets management following the AGENTS.md guidelines. All sensitive information is stored outside the project folder in `~/.config/sa-podcast/secrets.json`.

## Setup Instructions

### 1. Create the secrets directory
```bash
mkdir -p ~/.config/sa-podcast
```

### 2. Create your secrets file
Copy the template and fill in your actual credentials:

```bash
cp secrets.json.template ~/.config/sa-podcast/secrets.json
```

### 3. Edit your secrets file
Open `~/.config/sa-podcast/secrets.json` and fill in your actual API keys and credentials:

```json
{
  "openai_api_key": "sk-your-actual-openai-key-here",
  "claude_api_key": "sk-ant-your-actual-claude-key-here",
  "azure_speech_key": "your-actual-azure-speech-key-here",
  "azure_speech_region": "your-azure-region-here",
  "email": {
    "address": "your-email@gmail.com",
    "password": "your-app-password-here",
    "imap_server": "imap.gmail.com"
  },
  "cleanup": {
    "secret_key": "your-cleanup-secret-key-here"
  }
}
```

### 4. Get your API keys

#### OpenAI API Key
- Go to https://platform.openai.com/api-keys
- Create a new API key
- Copy it to `openai_api_key`

#### Claude API Key
- Go to https://console.anthropic.com/
- Create a new API key
- Copy it to `claude_api_key`

#### Azure Speech Service
- Go to https://portal.azure.com/
- Create a Cognitive Services Speech resource
- Copy the key to `azure_speech_key`
- Copy the region to `azure_speech_region`

#### Gmail App Password
- Go to your Google Account settings
- Enable 2-factor authentication
- Generate an App Password for "Mail"
- Use this as your `email.password` (NOT your regular Gmail password)

### 5. Test the setup
```bash
python summarize_transcript.py
```

## Security Benefits

✅ **No secrets in project files** - Everything is outside the repo  
✅ **No .env files** - Following AGENTS.md guidelines  
✅ **File-based secrets** - More secure than environment variables  
✅ **Git-safe** - Secrets never accidentally committed  
✅ **Outside project folder** - `~/.config/sa-podcast/secrets.json`  

## File Structure
```
~/.config/sa-podcast/
└── secrets.json          # Your actual secrets (NOT in git)

sa-news-podcast/
├── scripts/
│   └── secure_secrets.py # Loads secrets securely
├── secrets.json.template # Template for you to copy
└── SECURE_SETUP.md      # This guide
```
