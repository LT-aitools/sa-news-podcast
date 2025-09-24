# GitHub Actions Setup for Daily SA News Podcast

This guide explains how to set up automated daily podcast generation using GitHub Actions.

## 🚀 Overview

The workflow will:
1. **Run daily at 6:00 AM UTC** (8:00 AM SAST)
2. **Fetch AI news** from Perplexity, Claude, and ChatGPT
3. **Generate transcript** using Claude
4. **Create audio** using Microsoft TTS
5. **Assemble podcast** with music transitions
6. **Deploy files** for hosting

## 🔧 Required Setup

### 1. GitHub Secrets Configuration

You need to add these secrets to your GitHub repository:

**Go to:** `Settings` → `Secrets and variables` → `Actions` → `Repository secrets`

Add these secrets:

```
PERPLEXITY_API_KEY=your_perplexity_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here  
OPENAI_API_KEY=your_openai_api_key_here
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=your_azure_speech_region_here
CLEANUP_SECRET_KEY=your_cleanup_secret_key_here
```

### 2. API Keys Needed

- **Perplexity API**: Get from [Perplexity AI](https://www.perplexity.ai/settings/api)
- **Claude API**: Get from [Anthropic Console](https://console.anthropic.com/)
- **OpenAI API**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Azure Speech**: Get from [Azure Portal](https://portal.azure.com/)

### 3. Repository Settings

Enable GitHub Actions:
- Go to repository `Settings` → `Actions` → `General`
- Ensure "Allow all actions and reusable workflows" is selected

## 📅 Schedule Configuration

The workflow runs daily at **6:00 AM UTC** (8:00 AM SAST).

To change the schedule, edit `.github/workflows/daily-podcast.yml`:

```yaml
on:
  schedule:
    - cron: '0 6 * * *'  # 6:00 AM UTC daily
```

**Cron format:** `minute hour day month day-of-week`
- `0 6 * * *` = 6:00 AM UTC daily
- `0 8 * * *` = 8:00 AM UTC daily  
- `30 5 * * *` = 5:30 AM UTC daily

## 🔄 Manual Triggering

You can manually trigger the workflow:
1. Go to `Actions` tab in your repository
2. Select "Daily SA News Podcast" workflow
3. Click "Run workflow" button

## 📁 Generated Files

The workflow generates:
- `outputs/ai_news_digests.txt` - AI news summaries
- `outputs/latest_podcast_summary.txt` - Generated transcript
- `public/YYYY-MM-DD.mp3` - Final podcast audio
- `public/feed.xml` - Updated RSS feed

## 🚨 Error Handling

### Common Issues:

1. **API Key Failures**
   - Check secrets are correctly set
   - Verify API keys are valid and have credits
   - Check API rate limits

2. **TTS Failures**
   - Verify Azure Speech credentials
   - Check Azure Speech service status
   - Ensure text length is within limits

3. **File Generation Failures**
   - Check disk space in GitHub Actions
   - Verify file permissions
   - Check for missing dependencies

### Monitoring:

- Check `Actions` tab for workflow status
- Review logs for specific error messages
- Set up notifications for failures

## 🔧 Customization

### Change Schedule:
```yaml
on:
  schedule:
    - cron: '0 8 * * *'  # 8:00 AM UTC
```

### Add Notifications:
```yaml
- name: Notify on success
  if: success()
  run: |
    # Add webhook notification here
    curl -X POST "your-webhook-url" -d "Podcast generated successfully"
```

### Deploy to Different Host:
```yaml
- name: Deploy to custom host
  run: |
    # Add your deployment script here
    rsync -av public/ user@your-server:/path/to/podcast/
```

## 📊 Cost Considerations

**Estimated daily costs:**
- **Perplexity API**: ~$0.10-0.50 per day
- **Claude API**: ~$0.20-1.00 per day  
- **OpenAI API**: ~$0.10-0.50 per day
- **Azure Speech**: ~$0.50-2.00 per day

**Total**: ~$1-4 per day depending on usage

## 🛡️ Security Notes

- API keys are stored as GitHub Secrets (encrypted)
- Secrets are only available during workflow execution
- No secrets are logged or exposed in workflow logs
- Generated files are stored as artifacts (temporary)

## 🔍 Troubleshooting

### Workflow Not Running:
1. Check if Actions are enabled in repository settings
2. Verify cron schedule is correct
3. Check for syntax errors in workflow file

### API Failures:
1. Verify all secrets are set correctly
2. Check API key validity and credits
3. Review API rate limits and quotas

### File Generation Issues:
1. Check Python dependencies in requirements.txt
2. Verify file paths and permissions
3. Review error logs for specific issues

## 📞 Support

If you encounter issues:
1. Check the workflow logs in GitHub Actions
2. Review this documentation
3. Verify all secrets are correctly configured
4. Test the workflow manually first
