# GitHub Actions Setup Guide

## Security Approach ✅

This workflow uses **direct GitHub Secrets** (most secure approach):
- Secrets are never written to disk
- GitHub handles encryption/decryption
- No risk of secrets being logged or cached
- Works seamlessly with both local development and GitHub Actions

## Required GitHub Secrets

You need to add the following secrets to your GitHub repository:

### 1. OpenAI API Key
- **Secret Name**: `OPENAI_API_KEY`
- **Value**: Your OpenAI API key (starts with `sk-`)
- **How to get**: https://platform.openai.com/api-keys

### 2. Claude API Key
- **Secret Name**: `CLAUDE_API_KEY`
- **Value**: Your Anthropic Claude API key (starts with `sk-ant-`)
- **How to get**: https://console.anthropic.com/

### 3. Azure Speech Service
- **Secret Name**: `AZURE_SPEECH_KEY`
- **Value**: Your Azure Speech Service key
- **Secret Name**: `AZURE_SPEECH_REGION`
- **Value**: Your Azure Speech Service region (e.g., `eastus`)
- **How to get**: https://portal.azure.com/ → Create Speech Service resource

### 4. Email Credentials
- **Secret Name**: `EMAIL_ADDRESS`
- **Value**: Your Gmail address
- **Secret Name**: `EMAIL_PASSWORD`
- **Value**: Your Gmail App Password (not your regular password)
- **Secret Name**: `IMAP_SERVER`
- **Value**: `imap.gmail.com` (default)
- **How to get Gmail App Password**: 
  1. Enable 2-Factor Authentication on your Google account
  2. Go to https://myaccount.google.com/security
  3. Click "App passwords" → Generate password for "Mail"

### 5. Cleanup Secret Key
- **Secret Name**: `CLEANUP_SECRET_KEY`
- **Value**: Any random string (used for cleanup API security)
- **Example**: `my-super-secret-cleanup-key-123`

## How to Add Secrets

1. Go to your GitHub repository
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret with the exact name and value listed above

## Workflow Schedule

The workflow is set to run daily at:
- **Time**: 5:30 AM UTC (7:30 AM SAST)
- **Cron**: `'30 5 * * *'`

You can also trigger it manually via:
- **Actions** tab → **Daily Podcast Generation** → **Run workflow**

## What the Workflow Does

1. **Fetches News**: Pulls from RSS feeds and email newsletters
2. **Generates Transcript**: Uses OpenAI GPT-5-mini to create summary
3. **Fact-Checks**: Uses Claude to verify accuracy and context
4. **Final Edits**: Uses OpenAI GPT-5-mini to clean for TTS and fix issues
5. **Creates Audio**: Uses Azure Speech Service for text-to-speech
6. **Updates Feed**: Updates the podcast RSS feed
7. **Cleans Up**: Removes old episodes
8. **Commits**: Pushes changes to the repository

## Troubleshooting

### Common Issues

1. **"Secrets file not found"**
   - Check that all required secrets are added to GitHub
   - Verify secret names match exactly (case-sensitive)

2. **"API key not found"**
   - Verify the API key is valid and has sufficient credits
   - Check that the key format is correct

3. **"Email login failed"**
   - Use Gmail App Password, not your regular password
   - Ensure 2FA is enabled on your Google account

4. **"Transcript generation failed"**
   - Check that RSS feeds are accessible
   - Verify email credentials are correct
   - Check API rate limits

### Manual Testing

To test the workflow locally:

```bash
# 1. Set up secrets locally
mkdir -p ~/.config/sa-podcast
cp secrets.json.template ~/.config/sa-podcast/secrets.json
# Edit the file with your actual keys

# 2. Test transcript generation
python3 summarize_transcript.py

# 3. Test podcast creation
python3 podcast_creator.py

# 4. Test feed update
node api/podcast-feed.js
```

## File Structure

The workflow expects this structure:
```
├── .github/workflows/daily-podcast.yml
├── summarize_transcript.py
├── podcast_creator.py
├── api/podcast-feed.js
├── api/cleanup-old-episodes.js
├── requirements.txt
├── package.json
└── public/
    ├── feed.xml
    └── [episode files]
```
