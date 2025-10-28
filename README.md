# sa-news-podcast
Creating a short (4-5 min) daily weekday podcast, focused solely on South African news and all AI-generated.

## overview 
The podcast gets created by: 
1. Scraping news headlines/info from RSS feeds and email newsletters
2. AI summary / processing:
   - OpenAI GPT-5-mini generates initial 700-1000 word summary (transcript)
   - Claude fact-checks for accuracy, context, and neutrality
   - OpenAI GPT-5-mini final editor optimizes for text-to-speech
3. Assembling music & text-to-speech (using Azure), into a podcast 
4. Publishing that podcast in our RSS feed
5. Cleaning up old (>30 day) episodes, to prevent bloated hosting costs

## setup

### 1. Install the required Python packages:
`pip install -r requirements.txt`

### 2. Set up all the external emails and APIs, and add to a JSON file for local testing:
- Get OpenAI and Anthropic API tokens
- Sign up for a new gmail address (for receiving newsletters), and create a new "app password"
- Place API tokens and gmail app password info into a JSON file (placed outside this project repo) - Copy `secrets.json.template` as a template, and see `SECURE_SETUP.md` for full details.
- Sign up for email newsletters using that email address.
- Sign up for an Azure account, create a service for "Text to Speech," and then grab the API key (note: there's a big free tier, so this will likely be free!)

### 3. Edit the following to fit your country's parameters (if you don't want to use South Africa)
- `pull_rss_feeds.py` to include the RSS feeds of your country's main news providers
- `summarize_transcript.py` prompt to specifically include your country's info 
- `email_newsletter_retrieval.py` to include info related to your newsletters (e.g. sender, subject line, etc)

### 4. Run tests (in this order)
- Run `pull_rss_feeds.py` and see if creates a new file (`rss_feeds_content.txt`) with correct data from the RSS feed. 
- Run `email_newsletter_retrieval.py` and see if it creates a new file (`newsletter_content.txt`) with scraped info from the newsletter
- Run `summarize_transcript.py` to check that the summary it creates for your country's news works okay. 
- Run `podcast_creator.py` to check that it assembles the music and text-to-speech correctly, using your Azure keys. 

### 5. Set up for fully automation 🤖
Add these secrets to GitHub > Settings > Secrets and variables > Actions:
- `OPENAI_API_KEY` - Your OpenAI API key
- `CLAUDE_API_KEY` - Your Claude API key  
- `AZURE_SPEECH_KEY` - Your Azure Speech key
- `AZURE_SPEECH_REGION` - Your Azure region
- `EMAIL_ADDRESS` - Your Gmail address
- `EMAIL_PASSWORD` - Your Gmail App Password
- `CLEANUP_SECRET_KEY` - Any random string

### 6. Let it fly! 
The Github workflows will have this run daily at 5:30am UTC (7:30am SAST), to do the following:
   1. Set up environment
   2. Generate transcript (summarize_transcript.py)
   3. Create podcast (podcast_creator.py)
   4. Update podcast feed (podcast-feed.js)
   5. Clean up old episodes (cleanup-old-episodes.js)
   6. Commit and push changes
   See `GITHUB_ACTIONS_WORKFLOW.md` for full details.


## Hallucination 

Spot-checking suggested news summaries done this way are generally correct. We did however try using LLMs' web search capability to look up SA news from the last 24 hours and summarize it. This was a mess: 
- ChatGPT, Claude, and Perplexity basically never agreed on the main stories. (And running them multiple times in a row led to really different results.)
- The stories they chose were often not that important. 
- There were significant hallucinations, incorrect causal relationships (attempts to "tell a story" by linking unrelated news), etc.  
- It was pretty expensive, particularly if using ChatGPT (which also perfomred the best). Each podcast episode, if using multiple web earches + a summary transcript + an editor / fact-checker would cost a little over $1 per episode. 

We therefore decided NOT to go this route, and stick to the RSS feed + email newsletter information as the source material (with LLMs' web search capabilities turned off).

## SA News Sources ##
This project uses these South African news sources, for the podcast:

### RSS feeds from: 
- Daily Maverick
- Sunday Times / TimesLive 
- Mail & Guardian
- Google News (South Africa)

### Email newsletters from: 
- Daily Maverick (e.g. First Thing, Afternoon Thing)
- News24 
- The Herald

## Attribution

This repo is made with love & vibe coding by <a href= "https://letstalkaitools.com">Let's Talk AI Tools</a> -- a personal, not-for-profit project: just two product gals (and their chatbots) exploring the world of generative AI.
- Tools used: Claude & Cursor (for development), OpenAI GPT-5-mini (for writing & editing), Claude Sonnet 4.5 (for fact-checking), Azure TTS (for speech), Vercel (for hosting)

Intro/outtro music by <a href="https://pixabay.com/users/sonican-38947841/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=263720">Dvir Silver</a> from <a href="https://pixabay.com/music//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=263720">Pixabay</a>

Transition music by <a href="https://pixabay.com/users/ivan_luzan-34614814/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=154189">Ivan Luzan</a> from <a href="https://pixabay.com/music//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=154189">Pixabay</a>

