# ABOUTME: Claude-based transcript generator for SA News Podcast
# ABOUTME: Converts AI news digests into TTS-optimized podcast transcripts

import asyncio
import aiohttp
import json
import os
from datetime import datetime
import pytz
from typing import Optional, Dict, Any
from scripts.secure_secrets import get_secrets

class TranscriptGenerator:
    """
    Generates podcast transcripts from AI news digests using Claude API
    with the exact prompt specified in NewWorkflow.md.
    """
    
    def __init__(self):
        """Initialize the Transcript Generator with Claude API credentials."""
        self.secrets = get_secrets()
        self.sast_timezone = pytz.timezone('Africa/Johannesburg')
        
        # Exact transcript prompt from NewWorkflow.md
        self.transcript_prompt = """# Create a 4-5 minute (700-1000 words) daily news podcast transcript summarizing the biggest South African news for the day. A text-to-voice API will then read it, and then a Python script will intersperse it with transition music. 
- Use the news summaries in this TXT file for reference, slightly preferencing the AI news digests over the RSS feeds. Do not make anything else up. Only use the information given to you in the news digests file.
- Focus on the key stories, particularly on things that just happened (breaking news) or viral, and affecting many South Africans.
- Make it straight to the point and news-focused, with minimal preamble to each story. More important stories can receive more time / words. 
- Format the output as a natural podcast transcript for an AI named Leah to read.
- Make the introduction "Howzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah." - Mention today's date (in South African timezone) in the intro.
- Start the transcript with  intro music and end it with outro music  – written exactly like that (for the Python script to pick up.) Between major stories, add transition music . Do not include any other sound effects or music references. 
- Keep the end/sign-off super short.
# Since we'll be using text-to-voice APIs to generate the audio, make sure the transcript is clean and fit for that use case. For example: 
- Don't use bullet points or other things that text-to-voice might read strangely. Instead, introduce each story as a separate one. ("The next story…" or "In other news…" etc.)
- Use the expanded form of words, not contractions (for example: "cannot" instead of "can't" and "they are" instead of "they're").
- Write out numbers and value amounts (instead of "R500,000" - write "five hundred thousand rand" and instead of "1.25 million", write "one point two five million")"""
    
    def get_south_african_date(self) -> str:
        """
        Get today's date in South African timezone.
        
        Returns:
            Formatted date string for South African timezone
        """
        now_sast = datetime.now(self.sast_timezone)
        return now_sast.strftime('%A, %B %d, %Y')
    
    def read_news_digests_file(self, file_path: str) -> str:
        """
        Read the AI news digests file.
        
        Args:
            file_path: Path to the news digests file
            
        Returns:
            Content of the news digests file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ Read news digests from: {file_path}")
            return content
        except FileNotFoundError:
            print(f"❌ News digests file not found: {file_path}")
            return ""
        except Exception as e:
            print(f"❌ Error reading news digests: {e}")
            return ""
    
    async def generate_transcript(self, news_digests_content: str) -> Optional[str]:
        """
        Generate podcast transcript using Claude API.
        
        Args:
            news_digests_content: Content from AI news digests
            
        Returns:
            Generated transcript or None if failed
        """
        try:
            api_key = self.secrets.get_claude_api_key()
            
            # Get today's date in South African timezone
            today_date = self.get_south_african_date()
            
            # Prepare the full prompt with news digests and date
            full_prompt = f"{self.transcript_prompt}\n\nToday's date is {today_date}.\n\nNews digests to use:\n{news_digests_content}"
            
            # Claude API endpoint
            url = "https://api.anthropic.com/v1/messages"
            
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": "claude-sonnet-4-20250514",  # Use Claude Sonnet 4
                "max_tokens": 2000,  # Increased for longer transcripts
                "messages": [
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        transcript = data["content"][0]["text"]
                        print("✅ Transcript generated successfully")
                        return transcript
                    else:
                        error_text = await response.text()
                        print(f"❌ Claude API error: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"❌ Transcript generation error: {e}")
            return None
    
    def validate_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Validate that the transcript contains all required elements.
        
        Args:
            transcript: The generated transcript
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "word_count": len(transcript.split()),
            "character_count": len(transcript)
        }
        
        # Check for required elements
        required_elements = [
            ("intro_music", "intro music"),
            ("outro_music", "outro music"),
            ("leah_intro", "Howzit South Africa, and welcome to Mzansi Lowdown"),
            ("ai_host", "I am your A.I. host, Leah"),
            ("transition_music", "transition music")
        ]
        
        for element_name, element_text in required_elements:
            if element_text.lower() not in transcript.lower():
                validation_results["errors"].append(f"Missing required element: {element_name}")
                validation_results["is_valid"] = False
        
        # Check word count (should be 700-1000 words)
        word_count = validation_results["word_count"]
        if word_count < 700:
            validation_results["warnings"].append(f"Transcript is short ({word_count} words), should be 700-1000 words")
        elif word_count > 1000:
            validation_results["warnings"].append(f"Transcript is long ({word_count} words), should be 700-1000 words")
        
        # Check for TTS optimization issues
        tts_issues = []
        
        # Check for contractions (these will be handled by sanitize_text, but good to warn)
        contractions = ["can't", "won't", "don't", "isn't", "aren't", "wasn't", "weren't", "hasn't", "haven't", "hadn't", "wouldn't", "couldn't", "shouldn't", "they're", "we're", "you're", "it's", "that's", "there's", "here's"]
        
        for contraction in contractions:
            if contraction in transcript.lower():
                tts_issues.append(f"Contains contraction: {contraction} (will be expanded by sanitize_text)")
        
        # Check for apostrophes that might cause TTS issues
        if "'" in transcript or "'" in transcript or "'" in transcript:
            tts_issues.append("Contains apostrophes (will be removed by sanitize_text)")
        
        # Check for numbers that should be written out
        import re
        currency_pattern = r'R\d+[,.]?\d*'
        if re.search(currency_pattern, transcript):
            tts_issues.append("Contains currency amounts (should be written out for TTS)")
        
        large_number_pattern = r'\d+\.?\d*\s*(million|billion|thousand)'
        if re.search(large_number_pattern, transcript):
            tts_issues.append("Contains large numbers (should be written out for TTS)")
        
        if tts_issues:
            validation_results["warnings"].extend(tts_issues)
        
        return validation_results
    
    def save_transcript(self, transcript: str, output_file: str = "outputs/latest_podcast_summary.txt") -> str:
        """
        Save the generated transcript to a file.
        
        Args:
            transcript: The generated transcript
            output_file: Path to save the transcript
            
        Returns:
            Path to the saved file
        """
        try:
            # Create outputs directory if it doesn't exist
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            print(f"💾 Transcript saved to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error saving transcript: {e}")
            return ""
    
    async def generate_transcript_from_file(self, news_digests_file: str, output_file: str = "outputs/latest_podcast_summary.txt") -> Dict[str, Any]:
        """
        Complete workflow: read news digests, generate transcript, validate, and save.
        
        Args:
            news_digests_file: Path to the AI news digests file
            output_file: Path to save the generated transcript
            
        Returns:
            Dictionary with results and validation info
        """
        print("🚀 Starting transcript generation workflow...")
        
        # Read news digests
        news_content = self.read_news_digests_file(news_digests_file)
        if not news_content:
            return {
                "success": False,
                "error": "Failed to read news digests file",
                "transcript": None,
                "saved_file": "",
                "validation": None
            }
        
        # Generate transcript
        transcript = await self.generate_transcript(news_content)
        if not transcript:
            return {
                "success": False,
                "error": "Failed to generate transcript",
                "transcript": None,
                "saved_file": "",
                "validation": None
            }
        
        # Validate transcript
        validation = self.validate_transcript(transcript)
        
        # Save transcript
        saved_file = self.save_transcript(transcript, output_file)
        
        # Prepare results
        results = {
            "success": True,
            "error": None,
            "transcript": transcript,
            "saved_file": saved_file,
            "validation": validation
        }
        
        # Print validation results
        print(f"\n📊 Transcript Validation Results:")
        print(f"  Word count: {validation['word_count']}")
        print(f"  Character count: {validation['character_count']}")
        print(f"  Valid: {'✅ Yes' if validation['is_valid'] else '❌ No'}")
        
        if validation['errors']:
            print(f"  Errors: {', '.join(validation['errors'])}")
        
        if validation['warnings']:
            print(f"  Warnings: {', '.join(validation['warnings'])}")
        
        return results

    async def generate_transcript_from_multiple_sources(self, ai_digests_file: str, rss_file: str, output_file: str = "outputs/latest_podcast_summary.txt") -> Dict[str, Any]:
        """
        Generate transcript from both AI news digests and RSS feeds.
        
        Args:
            ai_digests_file: Path to the AI news digests file
            rss_file: Path to the RSS feeds summary file
            output_file: Path to save the generated transcript
            
        Returns:
            Dictionary with results and validation info
        """
        print("🚀 Starting transcript generation from multiple sources...")
        
        # Read AI news digests
        ai_content = self.read_news_digests_file(ai_digests_file)
        if not ai_content:
            return {
                "success": False,
                "error": "Failed to read AI news digests file",
                "transcript": None,
                "saved_file": "",
                "validation": None
            }
        
        # Read RSS feeds
        rss_content = self.read_news_digests_file(rss_file)
        if not rss_content:
            return {
                "success": False,
                "error": "Failed to read RSS feeds file",
                "transcript": None,
                "saved_file": "",
                "validation": None
            }
        
        # Combine both sources
        combined_content = f"""
COMBINED NEWS SOURCES FOR SOUTH AFRICAN PODCAST
==================================================
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

==================== AI NEWS SOURCES ====================
{ai_content}

==================== RSS FEED SOURCES ====================
{rss_content}
"""
        
        # Generate transcript from combined content
        transcript = await self.generate_transcript(combined_content)
        if not transcript:
            return {
                "success": False,
                "error": "Failed to generate transcript",
                "transcript": None,
                "saved_file": "",
                "validation": None
            }
        
        # Validate transcript
        validation = self.validate_transcript(transcript)
        
        # Save transcript
        saved_file = self.save_transcript(transcript, output_file)
        
        # Prepare results
        results = {
            "success": True,
            "error": None,
            "transcript": transcript,
            "saved_file": saved_file,
            "validation": validation
        }
        
        # Print validation results
        print(f"\n📊 Transcript Validation Results:")
        print(f"  Word count: {validation['word_count']}")
        print(f"  Character count: {validation['character_count']}")
        print(f"  Valid: {'✅ Yes' if validation['is_valid'] else '❌ No'}")
        
        if validation['errors']:
            print(f"  Errors: {', '.join(validation['errors'])}")
        
        if validation['warnings']:
            print(f"  Warnings: {', '.join(validation['warnings'])}")
        
        return results

async def main():
    """Test the Transcript Generator."""
    generator = TranscriptGenerator()
    
    print("🧪 Testing Transcript Generator...")
    
    # Test with a sample news digests file
    test_digests_file = "outputs/ai_news_digests.txt"
    
    if not os.path.exists(test_digests_file):
        print(f"❌ Test file not found: {test_digests_file}")
        print("Please run the AI News Fetcher first to generate news digests.")
        return
    
    results = await generator.generate_transcript_from_file(test_digests_file)
    
    if results["success"]:
        print(f"\n✅ Transcript generation successful!")
        print(f"📄 Saved to: {results['saved_file']}")
    else:
        print(f"\n❌ Transcript generation failed: {results['error']}")

if __name__ == "__main__":
    asyncio.run(main())
