# sa-news-podcast
Creating a short (3-5 min) daily weekday podcast, focused solely on South African news and all AI-generated.

## overview 
The podcast gets created by: 
1. Assembling news headlines/info from RSS feeds and email newsletters
2. Running that info through Gemini API, to create a 3-5 min transcript
3. Assembling music & text-to-speech (using Azure), into a podcast 
4. Publishing that podcast in our RSS feed
5. Cleaning up old (>30 day) episodes, to prevent bloated hosting costs

## setup

### 1. Install the required Python packages:
`python3 -m pip install requests python-dotenv google-generativeai beautifulsoup4 lxml azure-cognitiveservices-speech pydub requests`

### 2. Set up all the external emails and APIs, and add to an .env file, for local testing:
- Get a Gemini API token
- Sign up for a new gmail address (for receiving newsletters), and create a new "app password"
- Sign up for the email newsletter to that email address.
- Sign up for an Azure account, create a service for "Text to Speech," and then grab the API key (note: there's a big free tier, so this will likely be free!)

### 3. Edit the following to fit your country's parameters (if you don't want to use South Africa)
- `pull_rss_feeds.py` to include the RSS feeds of your country's main news providers
- `summarize_transcript.py` prompt to specifically include your country's info 
- `email_newsletter_retrieval.py` to include info related to your newsletters (e.g. sender, subject line, etc)

### 4. Run tests (in this order)
- Run `pull_rss_feeds.py` and see if creates a new file (`rss_feeds_content.txt`) with correct data from the RSS feed. 
- Run `email_newsletter_retrieval.py` and see if it creates a new file (`daily_maverick_first_thing.txt`) with scraped info from the newsletter
- Run `summarize_transcript.py` to check that the summary it creates for your country's news works okay. 
- Run `podcast_creator.py` to check that it assembles the music and text-to-speech correctly, using your Azure keys. 

### 5. Set up for fully automation 🤖
(A) Now set up for your Github actions / workflows to trigger correctly. 
Add all the items in your .env file to Github > Actions > Secrets, one by one.

### 6. Let it fly! 
The Github workflows will have this run daily at 7am UTC (9am SAST), to do the following:
   1. Set up environment
   2. Generate transcript (summarize_transcript.py)
   3. Create podcast (podcast_creator.py)
   4. Update podcast feed (podcast-feed.js)
   5. Clean up old episodes (cleanup-old-episodes.js)
   6. Commit and push changes


## Attribution

This repo is made with love & vibe coding by <a href= "https://letstalkaitools.com">Let's Talk AI Tools</a> -- a personal, not-for-profit project: just two product gals (and their chatbots) exploring the world of generative AI.
- Tools used: Claude & Cursor (for vibe coding), Gemini API & Azure TTS (for transcript & speech), Vercel (for hosting)

Intro/outtro music by <a href="https://pixabay.com/users/sonican-38947841/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=263720">Dvir Silver</a> from <a href="https://pixabay.com/music//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=263720">Pixabay</a>

Transition music by <a href="https://pixabay.com/users/ivan_luzan-34614814/?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=154189">Ivan Luzan</a> from <a href="https://pixabay.com/music//?utm_source=link-attribution&utm_medium=referral&utm_campaign=music&utm_content=154189">Pixabay</a>

