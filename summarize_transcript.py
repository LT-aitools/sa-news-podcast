import os
import time
from openai import OpenAI
import anthropic
from datetime import datetime
from scripts.pull_rss_feeds import get_all_rss_content
from scripts.email_newsletter_retrieval import get_latest_newsletter_content
from scripts.secure_secrets import get_openai_api_key, get_claude_api_key

# Configure APIs using secure secrets
client = OpenAI(api_key=get_openai_api_key())
claude_client = anthropic.Anthropic(api_key=get_claude_api_key())

def create_podcast_summary(newsletter_content, rss_content, max_retries=3):
    """Create a podcast summary using OpenAI API with retry logic"""
    
    # Create the prompt
    prompt = f"""You are a professional news editor creating podcast transcripts for South African news.

    Create a 4-5 minute (700-1000 words) daily news podcast transcript summarizing the biggest South African news for the day. 
    Focus on 3-5 key stories. Use ONLY the following sources - do not search the web or use any external information:

    EMAIL NEWSLETTER CONTENT:
    {newsletter_content}

    RSS FEEDS CONTENT:
    {rss_content}

    Format the output as a natural podcast transcript for an AI named Leah to read.
    Focus on South African news only. Don't include any purely international news unless they directly involve South Africa.
    Exclude sports news.
    Keep it between 700-1000 words.
    Make it straight to the point and news-focused, with minimal preamble to each story. Don't use bullet points.
    Start with the **intro music** marker. Then make the introduction "Howzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah."
    Mention today's date (in South African timezone) in the intro.
    Between each story, include transition music, marked as **transition music**. 
    Include succint transitions or introductions to each story, e.g. "First up" or "In economic news..." - Write the transcript for audio (to be listened to), not to be read. 
    Use the expanded form of words, not contractions (for example: "cannot" instead of "can't" and "they are" instead of "they're").
    Write out numbers and value amounts (instead of "R500,000" - write "five hundred thousand rand" and instead of "1.25 million", write "one point two five million")
    Keep the end/sign-off super short, like "That's all for today," followed by the **outro music** - Do not include long calls to action nor repeat the date / announcer's name. 
    Do not include any sound effects or music besides "intro music," "outtro music," and "transition music," which should be written as **intro music**, **transition music**, or **outro music** in the transcript. Include the transition music BETWEEN each story.


    IMPORTANT: Use ONLY the information provided in the sources above. Do not add any external information or make assumptions not supported by the provided content.
    """

    for attempt in range(max_retries):
        try:
            # Generate the summary using OpenAI GPT-5-mini
            # Note: No 'tools' parameter = no web search or external tools available
            response = client.responses.create(
                model="gpt-5-mini",  # Latest GPT-5-mini model
                input=prompt,
                reasoning={"effort": "low"},  # GPT-5 specific parameter
                text={"verbosity": "medium"},  # GPT-5 specific parameter
                max_output_tokens=2000
                # No 'tools' parameter = explicitly no web search or external tools
            )
            
            if response and response.output_text:
                return response.output_text
            else:
                print(f"Empty response from OpenAI API on attempt {attempt + 1}")
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
    print("All attempts to use OpenAI GPT-5-mini API failed. No transcript will be generated.")
    return None

def fact_check_transcript(transcript, newsletter_content, rss_content, max_retries=3):
    """Fact-check the generated transcript using Claude API with web search disabled"""
    
    fact_check_prompt = f"""You are a fact-checker for South African news. Your task is to evaluate this podcast transcript against ONLY the provided source materials. Do NOT use any external information or web search.

    Evaluate the transcript based on these four criteria:

    1. **ACCURACY [MOST IMPORTANT]**: Are all facts based on the sources given, with no fabricated hallucinations? Information must be presented with fidelity, hewing to the source information. Pay close attention to correctly representing chronology and causal relations (don't connect things that aren't connected). Do not generalize.

    2. **CONTEXT**: Is the context correct and sufficient? The answer should contain all relevant information for the news item to be informative and not misleading. However, if this context is not present in the source information, do not make it up; instead, provide as much context as possible.

    3. **OPINION ATTRIBUTION**: Are opinions flagged as opinions? Ensure specific viewpoints are not represented as facts, and that opinions are attributed to their source.

    4. **NEUTRALITY**: Is news presented neutrally, without editorialization? Avoid introducing opinions or editorial slants that may be misleading or non-transparent.

    TRANSCRIPT TO FACT-CHECK:
    {transcript}
    
    SOURCE MATERIALS (ONLY USE THESE):
    NEWSLETTER CONTENT:
    {newsletter_content}
    
    RSS FEEDS CONTENT:
    {rss_content}
    
    Please provide your evaluation in this format:
    
    SPECIFIC ISSUES FOUND:
    - ACCURACY:[List any specific factual errors]
    - CONTEXT:[List any missing context that should be included]
    - OPINION ATTRIBUTION:[List any opinions that should be attributed]
    - NEUTRALITY:[List any editorial bias or slant]
    
    RECOMMENDATIONS: [Specific corrections needed]
    """
    
    for attempt in range(max_retries):
        try:
            response = claude_client.messages.create(
                model="claude-sonnet-4-5-20250929",  # Latest Claude Sonnet 4.5
                max_tokens=2000,
                temperature=0.1,  # Low temperature for consistent fact-checking
                messages=[
                    {"role": "user", "content": fact_check_prompt}
                ]
            )
            
            if response and response.content[0].text:
                return response.content[0].text
            else:
                print(f"Empty response from Claude fact-checker on attempt {attempt + 1}")
                
        except Exception as e:
            print(f"Error in fact-checking attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
    
    print("All fact-checking attempts failed.")
    return "FACT_CHECK_FAILED: Unable to fact-check transcript."

def final_edit_transcript(transcript, fact_check_results, max_retries=3):
    """Final edit of transcript using Claude to address fact-check findings and clean for TTS"""
    
    edit_prompt = f"""You are a final editor for a South African news podcast transcript. Your task is to:

    1. **Address fact-check findings**: Review the fact-check results and make necessary corrections
    2. **Clean for Text-to-Speech**: Remove or replace symbols that would cause TTS issues
    3. **Ensure smooth reading**: Make the transcript flow naturally for an AI voice, and for listening (ie are there clear and succint transitions? Is the transition music placed in between each news story?)
    4. **Ensure top news**: Are the biggest, most important news stories mentioned by the source materials covered? Are insignificant news stories excluded?
    5. **Confirm SA focus**: Are purely international news excluded, unless they directly involve South Africa?

    ORIGINAL TRANSCRIPT:
    {transcript}

    FACT-CHECK RESULTS:
    {fact_check_results}

    CLEANING REQUIREMENTS:
    - KEEP asterisks around music markers (e.g., "**intro music**", "**transition music**", "**outro music**")
    - Remove stray asterisks or dashes used for bullet points or formatting
    - Remove apostrophes that cause TTS issues (e.g., "South Africa's" → "South Africas")
    - Remove any other symbols that might cause TTS pronunciation issues
    - Ensure proper spacing and punctuation
    - Fix any factual errors identified in the fact-check
    - Maintain the same structure and length (700-1000 words)
    - Write out numbers and value amounts (instead of "R500,000" - write "five hundred thousand rand" and instead of "1.25 million", write "one point two five million")



    Return the cleaned and corrected transcript ready for text-to-speech conversion.
    """
    
    for attempt in range(max_retries):
        try:
            response = claude_client.messages.create(
                model="claude-sonnet-4-5-20250929",  # Latest Claude Sonnet 4.5
                max_tokens=2000,
                temperature=0.3,  # Slightly higher for creative editing
                messages=[
                    {"role": "user", "content": edit_prompt}
                ]
            )
            
            if response and response.content[0].text:
                # Clean the response to remove any markdown headers
                cleaned_text = response.content[0].text
                
                # Remove common markdown headers that might be added
                lines = cleaned_text.split('\n')
                cleaned_lines = []
                
                for line in lines:
                    # Skip lines that start with markdown headers
                    if line.strip().startswith('# '):
                        continue
                    # Skip lines that are just markdown headers
                    if line.strip() == '# FINAL EDITED TRANSCRIPT':
                        continue
                    cleaned_lines.append(line)
                
                return '\n'.join(cleaned_lines)
            else:
                print(f"Empty response from Claude final editor on attempt {attempt + 1}")
                
        except Exception as e:
            print(f"Error in final editing attempt {attempt + 1}: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
    
    print("All final editing attempts failed.")
    return transcript  # Return original if editing fails

def get_latest_newsletter_content():
    """
    Retrieves the content of the latest two Daily Maverick newsletters.
    """
    try:
        # Read the Daily Maverick newsletter content
        with open('outputs/newsletter_content.txt', 'r', encoding='utf-8') as f:
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
        with open("outputs/newsletter_content.txt", "w", encoding="utf-8") as f:
            combined_content = ""
            for newsletter in newsletters:
                print(f"Retrieved: {newsletter['subject']} ({newsletter['date']})")
                print("\nEXCERPT:")
                print(newsletter['content'][:200] + "...\n")
                combined_content += f"=== {newsletter['subject']} - {newsletter['date']} ===\n\n"
                combined_content += newsletter['content'] + "\n\n"
            f.write(combined_content)
            print("\nFull newsletters saved to outputs/newsletter_content.txt")
    else:
        print("No recent newsletters found - clearing old content")
        with open("outputs/newsletter_content.txt", "w", encoding="utf-8") as f:
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
        final_transcript = None
    else:
        print("\nGenerating podcast summary...")
        try:
            # Step 1: Generate initial summary using OpenAI
            summary = create_podcast_summary(newsletter_content, rss_content)
            
            if summary:
                # Save the original OpenAI transcript
                with open("outputs/openai_original_transcript.txt", "w", encoding="utf-8") as f:
                    f.write(summary)
                print("✅ OpenAI original transcript saved to: outputs/openai_original_transcript.txt")
                
                print("\nFact-checking transcript...")
                # Step 2: Fact-check the transcript using Claude
                fact_check_results = fact_check_transcript(summary, newsletter_content, rss_content)
                
                if fact_check_results:
                    # Save the fact-checker report
                    with open("outputs/fact_checker_report.txt", "w", encoding="utf-8") as f:
                        f.write(fact_check_results)
                    print("✅ Fact-checker report saved to: outputs/fact_checker_report.txt")
                
                print("\nFinal editing transcript...")
                # Step 3: Final edit to address fact-check findings and clean for TTS
                final_transcript = final_edit_transcript(summary, fact_check_results)
                
                if final_transcript:
                    # Save the final edited transcript (this is what gets passed to Azure TTS)
                    with open("outputs/latest_podcast_transcript.txt", "w", encoding="utf-8") as f:
                        f.write(final_transcript)
                    print("✅ Final transcript saved to: outputs/latest_podcast_transcript.txt")
            else:
                final_transcript = None
                
        except Exception as e:
            print(f"\nError: Failed to generate podcast summary: {e}")
            final_transcript = None
    
    # Final transcript is already saved above if successful
    if final_transcript is None:
        print("\nNo podcast transcript was generated. The podcast creator will skip this episode.")
    else:
        print("\nFinal podcast transcript has been generated and saved to outputs/latest_podcast_transcript.txt")

if __name__ == "__main__":
    main()