# Overview 
The goal of this project is to create an automated daily podcast focused on South African news. 

# Current workflow 
Currently, the workflow goes as follows:
1. We scrape text from the RSS feeds of various local South African news sources and one email newsletter.
2. We use Gemini API to summarize that news and turn it into a podcast transcript.
3. We have Microsoft Text-to-Speech API create audio from that text
4. We separate out that audio into different clips so that we can insert the musical transitions and intro/outro into it
5. We assemble the full podcast episode host that episode, deploying it and then adding it to the RSS feed so that the podcast apps can pick up the new episode

# Problems with this workflow 
1. The data fed into it isn't very good. Previously, there was a daily news email newsletter that was getting sent, but the newspaper that sent that has stopped it. So now this workflow is reliant purely on RSS feeds, which just have the headlines and one small lead sentence. That's often not enough information to build a good daily news podcast off of. There's just not enough rich context.
2. Gemini API isn't great. Previously, we were using it because it was a free option. But now that we've run through our free trial period, it would be better to use a more intelligent AI system like Anthropic's Claude.
3. Microsoft Text-to-Speech is generally okay, but it struggles with any sort of word with an apostrophe, so for instance, if something is "South Africa's problems", it will read it as "South Africa ess problem".

# New, improved workflow 
We thereby want to make a few changes to improve the quality of the Daily News podcast. The new workflow should be as follows:
1. Run the same web search prompt to find & summarize South African daily news through three different AI systems: Perplexity, Claude, and ChatGPT. 
2. Have Claude read through the Daily News Digests of those three systems and then assemble a podcast transcript based on it. 
3. The remainder of the workflow remains the same. We use Microsoft Text-to-Speech, and then assemble the same sound and music. However, I would like some help fixing the problem with the apostrophes.

## Prompts 
I've already tested and tweaked the prompts, so I want to use these ones precisely:
1. Web search prompt (for Perplexity, Claude, ChatGPT)
```
What are today's most important and widely-discussed South African news stories? Focus on: 1) Breaking national and regional news and major developments 2) Viral stories getting significant attention 3) Notable events affecting many people 4) Surprising or unusual stories gaining traction.
Give me a few sentences on each story. 
Ignore purely international stories that don’t involve South Africa.
```

2. Summary transcript prompt (for Claude):
```# Create a 4-5 minute (700-1000 words) daily news podcast transcript summarizing the biggest South African news for the day. A text-to-voice API will then read it, and then a Python script will intersperse it with transition music. 
- Use the news summaries in this TXT file for reference, slightly preferencing the AI news digests over the RSS feeds. Do not make anything else up. Only use the information given to you in the news digests file.
- Focus on the key stories, particularly on things that just happened (breaking news) or viral, and affecting many South Africans.
- Make it straight to the point and news-focused, with minimal preamble to each story. More important stories can receive more time / words. 
- Format the output as a natural podcast transcript for an AI named Leah to read.
- Make the introduction "Howzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah." - Mention today's date (in South African timezone) in the intro.
- Start the transcript with  intro music and end it with outro music  – written exactly like that (for the Python script to pick up.) Between major stories, add transition music . Do not include any other sound effects or music references. 
- Keep the end/sign-off super short.
# Since we’ll be using text-to-voice APIs to generate the audio, make sure the transcript is clean and fit for that use case. For example: 
- Don't use bullet points or other things that text-to-voice might read strangely. Instead, introduce each story as a separate one. (“The next story…” or “In other news…” etc.)
- Use the expanded form of words, not contractions (for example: "cannot" instead of "can't" and "they are" instead of "they're").
- Write out numbers and value amounts (instead of "R500,000" - write "five hundred thousand rand" and instead of "1.25 million", write "one point two five million")
```

## Models
I'd like to use: 
- OpenAI: gpt-5	with web search
- Anthropic: Claude Sonnet 4 (`claude-sonnet-4-20250514`) with web search (`web_search`)
- Perplexity: Sonar

# Coding these changes 
- *Project management*: I would like to check how we're doing with our different tasks by connecting to Linear. We're going to start by figuring out what needs to be done, creating tickets for them in Linear which is connected through an MCP, and then going through each ticket and marking them as complete within Linear as we're going through them.
- *Security*: As per the security guidelines in the @AGENTS.md  doc, I want to make sure that all of my API keys are outside of this project folder and instead in the .config/sa-podcast folder. 
