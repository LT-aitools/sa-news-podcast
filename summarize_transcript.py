import os
import time
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
from scripts.pull_rss_feeds import get_all_rss_content
from scripts.email_newsletter_retrieval import get_latest_newsletter_content

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def create_podcast_summary(newsletter_content, rss_content, max_retries=3):
    """Create a podcast summary using Gemini API with retry logic"""
    # Initialize Gemini model - using Flash-Lite for higher rate limits
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    # Create the prompt
    prompt = f"""Create a 3-5 minute (500-800 words) daily news podcast transcript summarizing the latest South African news for the day. 
    Focus on 3-5 key stories, excluding sports. Use the following sources:

    EMAIL NEWSLETTER CONTENT:
    {newsletter_content}

    RSS FEEDS CONTENT:
    {rss_content}

    Format the output as a natural podcast transcript for an AI named Leah to read.
    Focus on South African news only. Remove any international or US news.
    Exclude sports news.
    Keep it between 500-800 words.
    Make it engaging and conversational, as if someone is speaking to the audience.
    Make the introduction "Sawubona South Africa, and welcome to Mzansi Lowdown, your daily dose of the most important news coming out of the Republic. I'm your host, Leah."
    Mention today's date (in South African timezone) in the intro.
    Do not include any sound effects or music besides "intro music," "outtro music," and "transition music."
    """

    for attempt in range(max_retries):
        try:
            # Generate the summary
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "ResourceExhausted" in str(e) and attempt < max_retries - 1:
                # Get retry delay from error message if available
                retry_seconds = 2  # Shorter wait time since Flash-Lite has higher rate limits
                if "retry_delay" in str(e):
                    try:
                        retry_seconds = int(str(e).split("seconds:")[1].split("}")[0].strip())
                    except:
                        pass
                print(f"Rate limit hit. Waiting {retry_seconds} seconds before retry...")
                time.sleep(retry_seconds)
                continue
            else:
                print(f"Error generating content after {attempt + 1} attempts: {e}")
                raise
    
    return "Error: Failed to generate content after multiple attempts."

def get_latest_newsletter_content():
    """
    Retrieves the content of the latest two Daily Maverick newsletters.
    """
    try:
        # Read the Daily Maverick newsletter content
        with open('outputs/daily_maverick_first_thing.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"Error reading newsletter content: {e}")
        return "Error: Could not retrieve newsletter content."

def main():
    print("Starting podcast summary generation...")
    
    # First, fetch new newsletters
    print("\nFetching newsletter content...")
    from scripts.email_newsletter_retrieval import fetch_newsletter_from_email
    newsletters = fetch_newsletter_from_email()
    if not newsletters:
        print("Warning: Could not fetch new newsletters, will use existing content if available")
    
    # Get content from all sources
    newsletter_content = get_latest_newsletter_content()
    
    print("\nFetching RSS feeds content...")
    rss_content = get_all_rss_content()
    
    print("\nGenerating podcast summary...")
    try:
        # Generate summary using Gemini with retry logic
        summary = create_podcast_summary(newsletter_content, rss_content)
        
        # Save summary to file
        with open("outputs/latest_podcast_summary.txt", "w", encoding="utf-8") as f:
            f.write(summary)
        
        print("\nPodcast summary has been generated and saved to outputs/latest_podcast_summary.txt")
    except Exception as e:
        print(f"\nError: Failed to generate podcast summary: {e}")

if __name__ == "__main__":
    main()