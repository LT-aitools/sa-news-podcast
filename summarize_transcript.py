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
    prompt = f"""Create a 3-5 minute (500-1000 words) daily news podcast transcript summarizing the biggest South African news for the day. 
    Focus on 3-5 key stories, excluding sports. Use the following sources:

    EMAIL NEWSLETTER CONTENT:
    {newsletter_content}

    RSS FEEDS CONTENT:
    {rss_content}

    Format the output as a natural podcast transcript for an AI named Leah to read.
    Focus on South African news only. Don't include any purely international news unless they directly involve South Africa.
    Exclude sports news.
    Keep it between 500-1000 words.
    Make it straight to the point and news-focused, with minimal preamble to each story. Don't use bullet points.
    Make the introduction "Howzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I'm your A.I. host, Leah."
    Mention today's date (in South African timezone) in the intro.
    Write out numbers and value amounts (instead of "R500,000" - write "five hundred thousand rand" and instead of "1.25 million", write "one point two five million")
    Do not include any sound effects or music besides "intro music," "outtro music," and "transition music," which should be written as **intro music**, **transition music**, or **outro music** in the transcript.
    Keep the end/sign-off super short.
    """

    for attempt in range(max_retries):
        try:
            # Generate the summary
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
            else:
                print(f"Empty response from Gemini API on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {str(e)}")
            if "ResourceExhausted" in str(e) and attempt < max_retries - 1:
                retry_seconds = 2
                if "retry_delay" in str(e):
                    try:
                        retry_seconds = int(str(e).split("seconds:")[1].split("}")[0].strip())
                    except:
                        pass
                print(f"Rate limit hit. Waiting {retry_seconds} seconds before retry...")
                time.sleep(retry_seconds)
                continue
            elif attempt < max_retries - 1:
                time.sleep(2)
                continue
    
    # If we get here, all attempts failed
    print("All attempts to use Gemini API failed. No transcript will be generated.")
    return None

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
    
    # Write newsletters to file if we got any
    if newsletters:
        with open("outputs/daily_maverick_first_thing.txt", "w", encoding="utf-8") as f:
            combined_content = ""
            for newsletter in newsletters:
                print(f"Retrieved: {newsletter['subject']} ({newsletter['date']})")
                print("\nEXCERPT:")
                print(newsletter['content'][:200] + "...\n")
                combined_content += f"=== {newsletter['subject']} - {newsletter['date']} ===\n\n"
                combined_content += newsletter['content'] + "\n\n"
            f.write(combined_content)
            print("\nFull newsletters saved to outputs/daily_maverick_first_thing.txt")
    else:
        print("No recent newsletters found - clearing old content")
        with open("outputs/daily_maverick_first_thing.txt", "w", encoding="utf-8") as f:
            f.write("NO_RECENT_CONTENT: No newsletters found within the last 24 hours.")
    
    # Get content from all sources
    newsletter_content = get_latest_newsletter_content()
    
    print("\nFetching RSS feeds content...")
    rss_content = get_all_rss_content()
    
    # Check if we have any content to work with
    no_newsletter_content = "NO_RECENT_CONTENT" in newsletter_content if newsletter_content else True
    no_rss_content = not rss_content or rss_content.strip() == ""
    
    if no_newsletter_content and no_rss_content:
        print("\nNo recent content available - no transcript will be generated.")
        summary = None
    else:
        print("\nGenerating podcast summary...")
        try:
            # Generate summary using Gemini with retry logic
            summary = create_podcast_summary(newsletter_content, rss_content)
        except Exception as e:
            print(f"\nError: Failed to generate podcast summary: {e}")
            summary = None
    
    # Save summary to file
    with open("outputs/latest_podcast_summary.txt", "w", encoding="utf-8") as f:
        if summary is None:
            f.write("NO_TRANSCRIPT_GENERATED")
        else:
            f.write(summary)
    
    if summary is None:
        print("\nNo podcast summary was generated. The podcast creator will skip this episode.")
    else:
        print("\nPodcast summary has been generated and saved to outputs/latest_podcast_summary.txt")

if __name__ == "__main__":
    main()