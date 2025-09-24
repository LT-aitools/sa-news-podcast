# ABOUTME: Main podcast creation script for SA News Podcast
# ABOUTME: Handles text-to-speech conversion and audio assembly with music

import os
import time
import re
import tempfile
import requests
from datetime import datetime
import json
import html
import io
import wave
import asyncio
import sys
from scripts.secure_secrets import get_secrets

def sanitize_text(text):
    """
    Sanitize text for speech synthesis by removing special characters
    that might cause issues with the text-to-speech API, especially apostrophes
    that cause Microsoft TTS to mispronounce words.
    
    Args:
        text (str): The input text
        
    Returns:
        str: Sanitized text optimized for Microsoft TTS
    """
    # Sanitize text for speech synthesis
    
    # Replace problematic characters, curly quotes with straight quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('—', '-').replace('–', '-')
    text = text.replace('…', '...')
    
    # Comprehensive apostrophe removal to fix Microsoft TTS pronunciation issues
    # This prevents "South Africa's" from being read as "South Africa ess"
    text = text.replace("'", "")  # Standard apostrophe
    text = text.replace("'", "")  # Curly apostrophe
    text = text.replace("'", "")  # Another curly apostrophe variant
    text = text.replace("`", "")  # Grave accent (sometimes used as apostrophe)
    
    # Handle specific contractions that might still cause issues
    # These are common contractions that TTS might mispronounce
    contractions_map = {
        "cant": "cannot",
        "wont": "will not", 
        "dont": "do not",
        "isnt": "is not",
        "arent": "are not",
        "wasnt": "was not",
        "werent": "were not",  # Must come before "were" to avoid partial matches
        "hasnt": "has not",
        "havent": "have not",
        "hadnt": "had not",
        "wouldnt": "would not",
        "couldnt": "could not",
        "shouldnt": "should not",
        "theyre": "they are",
        "youre": "you are",
        "thats": "that is",
        "theres": "there is",
        "heres": "here is"
    }
    
    # Apply contraction expansions (case-insensitive but preserve capitalization)
    # Sort by length (longest first) to avoid partial matches
    sorted_contractions = sorted(contractions_map.items(), key=lambda x: len(x[0]), reverse=True)
    
    for contraction, expansion in sorted_contractions:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(contraction) + r'\b'
        
        def replace_contraction(match):
            matched_text = match.group(0)
            # Preserve the capitalization of the original contraction
            if matched_text[0].isupper():
                return expansion[0].upper() + expansion[1:]
            else:
                return expansion
        
        text = re.sub(pattern, replace_contraction, text, flags=re.IGNORECASE)
    
    # Replace emojis and other special characters with spaces
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    
    # Replace newlines with spaces to prevent pauses
    text = re.sub(r'\n+', ' ', text)
    
    # Remove extra spaces
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()

def filter_sound_effects(text):
    """
    Filter out sound effect references and speaker markers from the text
    while preserving the actual content
    
    Args:
        text (str): The input text
        
    Returns:
        str: Text with sound effects and speaker markers removed but content preserved
    """
    # Remove Leah: markers (with or without asterisks)
    text = re.sub(r'\*\*Leah:\*\*\s*|\bLeah:\s*', '', text)
    
    # Remove music markers explicitly
    text = text.replace("**Intro music**", "")
    text = text.replace("**Transition music**", "")
    text = text.replace("**Outro music**", "")
    
    # Clean up multiple newlines and spaces
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()

def extract_sections(text):
    """
    Extract sections from the text based on sound effect markers
    
    Args:
        text (str): The input text
        
    Returns:
        list: List of tuples containing (text, music_type)
    """
    sections = []
    current_text = []
    
    for line in text.split('\n'):
        # Check for music marker matches (case-insensitive)
        line_lower = line.lower()
        if 'intro music' in line_lower:
            if current_text:
                # Filter the accumulated text before adding
                clean_text = filter_sound_effects('\n'.join(current_text))
                if clean_text:
                    sections.append((clean_text, None))
                current_text = []
            sections.append((None, 'intro'))
        elif 'transition music' in line_lower:
            if current_text:
                clean_text = filter_sound_effects('\n'.join(current_text))
                if clean_text:
                    sections.append((clean_text, None))
                current_text = []
            sections.append((None, 'transition'))
        elif 'outro music' in line_lower:
            if current_text:
                clean_text = filter_sound_effects('\n'.join(current_text))
                if clean_text:
                    sections.append((clean_text, None))
                current_text = []
            sections.append((None, 'outro'))
        else:
            current_text.append(line)
    
    # Don't forget any remaining text
    if current_text:
        clean_text = filter_sound_effects('\n'.join(current_text))
        if clean_text:
            sections.append((clean_text, None))
    
    return [(text, music) for text, music in sections if text or music]

def text_to_speech_rest(text, output_file=None):
    """
    Convert text to speech using Microsoft Azure Text-to-Speech REST API
    
    Args:
        text (str): The text to convert to speech
        output_file (str, optional): Path to save the audio file. If None, will use a temporary file
        
    Returns:
        str: Path to the generated audio file
    """
    # Get Azure credentials from secure secrets
    try:
        secrets = get_secrets()
        subscription_key = secrets.get_azure_speech_key()
        region = secrets.get_azure_speech_region()
    except Exception as e:
        print(f"Error: Failed to load Azure Speech credentials: {e}")
        return None
    
    print(f"Using Azure Speech region: {region}")
    
    # If no output file specified, create a temporary one
    if output_file is None:
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        output_file = temp_file.name
        temp_file.close()
    
    try:
        # Get access token
        token_url = f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key
        }
        response = requests.post(token_url, headers=headers)
        access_token = str(response.text)
        
        # Prepare synthesis request
        url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'riff-24khz-16bit-mono-pcm',  # WAV format
            'User-Agent': 'SA News Podcast'
        }
        
        # Create SSML with 1.1x speed
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-ZA">
            <voice name="en-ZA-LeahNeural">
                <prosody rate="1.1">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        # Make synthesis request
        response = requests.post(url, headers=headers, data=ssml.encode('utf-8'))
        
        if response.status_code == 200:
            # Save the audio
            with open(output_file, 'wb') as f:
                f.write(response.content)
            print(f"Speech synthesis successful. Audio saved to {output_file}")
            return output_file
        else:
            print(f"Error: Speech synthesis failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error during text-to-speech conversion: {e}")
        if os.path.exists(output_file):
            os.remove(output_file)
        return None

def convert_audio_ffmpeg(input_file, output_file, input_format='wav', output_format='mp3'):
    """
    Convert audio using ffmpeg
    
    Args:
        input_file (str): Path to input audio file
        output_file (str): Path to save the output audio file
        input_format (str): Format of input file ('wav' or 'mp3')
        output_format (str): Desired output format ('wav' or 'mp3')
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Converting {input_file} to {output_format}")
        
        # Use ffmpeg to convert the file
        # -y: Overwrite output file if it exists
        # -i: Input file
        # -acodec: Audio codec (libmp3lame for MP3)
        # -ab: Audio bitrate (192k for good quality)
        # -ar: Audio sample rate (44100 Hz is standard)
        command = f'ffmpeg -y -i "{input_file}" -acodec libmp3lame -ab 192k -ar 44100 "{output_file}"'
        
        # Run the command
        result = os.system(command)
        
        if result == 0:
            print(f"Audio conversion successful. Saved to {output_file}")
            return True
        else:
            print(f"Error: ffmpeg conversion failed with exit code {result}")
            return False
            
    except Exception as e:
        print(f"Error converting audio: {e}")
        return False

def download_audio_data(url):
    """Download audio file and return the data as bytes"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return io.BytesIO(response.content)
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None

def normalize_wav_file(input_file, output_file=None):
    """
    Normalize WAV file to standard parameters (44.1kHz, stereo)
    using ffmpeg
    
    Args:
        input_file (str): Path to input WAV file
        output_file (str): Path to save normalized WAV file. If None, creates temp file
        
    Returns:
        str: Path to normalized WAV file, or None if failed
    """
    try:
        if output_file is None:
            temp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            output_file = temp.name
            temp.close()
            
        # Convert to standard format (44.1kHz stereo)
        command = f'ffmpeg -y -i "{input_file}" -acodec pcm_s16le -ac 2 -ar 44100 "{output_file}"'
        result = os.system(command)
        
        if result == 0:
            print(f"Normalized audio file: {output_file}")
            return output_file
        else:
            print(f"Error: Failed to normalize audio file")
            if os.path.exists(output_file):
                os.remove(output_file)
            return None
            
    except Exception as e:
        print(f"Error normalizing audio: {e}")
        if output_file and os.path.exists(output_file):
            os.remove(output_file)
        return None

def concatenate_wav_files(file_list, output_file):
    """
    Concatenate multiple WAV files into a single WAV file
    
    Args:
        file_list (list): List of WAV file paths
        output_file (str): Path to save the combined WAV file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Concatenating {len(file_list)} WAV files to {output_file}")
        
        # Create a temporary directory for normalized files
        temp_dir = tempfile.mkdtemp()
        normalized_files = []
        
        # Normalize each file to standard format
        for i, wav_file in enumerate(file_list):
            print(f"Normalizing file {i+1}/{len(file_list)}: {wav_file}")
            normalized_file = os.path.join(temp_dir, f"normalized_{i}.wav")
            result = normalize_wav_file(wav_file, normalized_file)
            if result:
                normalized_files.append(normalized_file)
            else:
                print(f"Error: Failed to normalize {wav_file}")
                # Clean up
                for f in normalized_files:
                    if os.path.exists(f):
                        os.remove(f)
                os.rmdir(temp_dir)
                return False
        
        # Create a file list for ffmpeg
        list_file = os.path.join(temp_dir, "files.txt")
        with open(list_file, 'w') as f:
            for file in normalized_files:
                f.write(f"file '{file}'\n")
        
        # Use ffmpeg to concatenate all files
        command = f'ffmpeg -y -f concat -safe 0 -i "{list_file}" -c copy "{output_file}"'
        result = os.system(command)
        
        # Clean up temporary files
        for f in normalized_files:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(list_file):
            os.remove(list_file)
        os.rmdir(temp_dir)
        
        if result == 0:
            print(f"Successfully created concatenated WAV file: {output_file}")
            return True
        else:
            print(f"Error: Failed to concatenate WAV files")
            return False
            
    except Exception as e:
        print(f"Error concatenating WAV files: {e}")
        return False

def create_podcast_with_music(transcript_file, output_file=None):
    """
    Create a podcast with text-to-speech and music in podcast-standard format
    
    Args:
        transcript_file (str): Path to the transcript file
        output_file (str): Path to save the final audio file. If None, will use current date
    """
    try:
        # If no output file specified, create one with today's date
        if output_file is None:
            current_date = datetime.now().strftime('%Y-%m-%d')
            output_file = f"public/{current_date}.mp3"
        
        # Create a temporary WAV file for the combined audio
        temp_wav_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
        
        # Read the transcript file
        with open(transcript_file, 'r', encoding='utf-8') as f:
            text = f.read()
            print(f"\nRead transcript file: {len(text)} characters")
        
        # Extract sections with music markers
        sections = extract_sections(text)
        print(f"Extracted {len(sections)} sections")
        
        # Prepare paths to music files (using WAV versions)
        intro_music_path = "public/DvirSilver_intro.wav"
        transition_music_path = "public/IvanLuzan_transition.wav"
        outro_music_path = "public/DvirSilver_intro.wav"  # Using intro music for outro too
        
        # Verify music files exist
        for music_file in [intro_music_path, transition_music_path]:
            if not os.path.exists(music_file):
                print(f"Error: Music file {music_file} not found")
                return False
        
        # Process each section and collect WAV files
        audio_files = []
        intro_played = False
        
        for i, (section_text, music_type) in enumerate(sections):
            print(f"\nProcessing section {i+1}/{len(sections)}")
            
            if music_type:
                print(f"Adding {music_type} music")
                # Add appropriate music
                if music_type == "intro":
                    if not intro_played:
                        audio_files.append(intro_music_path)
                        intro_played = True
                    else:
                        print("Skipping duplicate intro music")
                elif music_type == "transition":
                    audio_files.append(transition_music_path)
                elif music_type == "outro":
                    audio_files.append(outro_music_path)
            
            elif section_text:
                # If this is the first section and we haven't played intro yet, play it
                if i == 0 and not intro_played:
                    print("Adding initial intro music")
                    audio_files.append(intro_music_path)
                    intro_played = True
                
                print(f"Converting text section of length {len(section_text)}")
                
                # Simple splitting for TTS - keep chunks manageable
                max_chunk_len = 4500  # Adjust if needed
                chunks = []
                current_pos = 0
                while current_pos < len(section_text):
                    end_pos = min(current_pos + max_chunk_len, len(section_text))
                    # Try to find a sentence break near the end
                    sentence_break = section_text.rfind('.', current_pos, end_pos)
                    if sentence_break != -1 and end_pos < len(section_text):
                        end_pos = sentence_break + 1
                    
                    chunks.append(section_text[current_pos:end_pos])
                    current_pos = end_pos
                    
                print(f"Split into {len(chunks)} chunks for TTS")
                
                for j, chunk in enumerate(chunks):
                    if not chunk.strip(): # Skip empty chunks
                        continue
                    print(f"\nProcessing chunk {j+1}/{len(chunks)}")
                    audio_file = text_to_speech_rest(sanitize_text(chunk))
                    if audio_file:
                        audio_files.append(audio_file)
                    else:
                        print("Warning: Failed to generate audio for chunk")
        
        # Check if we have any audio content
        if not audio_files:
            print("Error: No audio content was generated")
            return False
        
        # Concatenate all WAV files
        print(f"\nConcatenating {len(audio_files)} audio segments")
        if not concatenate_wav_files(audio_files, temp_wav_file):
            print("Error: Failed to concatenate audio files")
            return False
        
        # Convert the final WAV file to MP3 using ffmpeg
        print(f"\nConverting final WAV file to MP3: {output_file}")
        if not convert_audio_ffmpeg(temp_wav_file, output_file, 'wav', 'mp3'):
            print("Error: Failed to convert to MP3")
            return False
        
        print(f"Podcast created successfully: {output_file}")
        
        # Clean up temporary files
        try:
            # Only clean up the temporary files we created, not the original WAV music files
            temp_files = [f for f in audio_files if f.startswith(tempfile.gettempdir())]
            temp_files.append(temp_wav_file)
            for file in temp_files:
                if os.path.exists(file):
                    os.remove(file)
        except Exception as e:
            print(f"Warning: Error cleaning up temporary files: {e}")
        
        return True
    
    except Exception as e:
        print(f"Error creating podcast: {e}")
        return False

async def generate_ai_podcast_content():
    """
    Generate podcast content using the new AI-powered workflow.
    
    Returns:
        tuple: (success: bool, transcript_file: str, error_message: str)
    """
    try:
        print("🤖 Starting AI-powered podcast content generation...")
        
        # Import AI modules
        from scripts.ai_news_fetcher import AINewsFetcher
        from scripts.transcript_generator import TranscriptGenerator
        
        # Step 1: Fetch AI news
        print("\n📰 Fetching news from AI sources...")
        fetcher = AINewsFetcher()
        news_summaries, digests_file = await fetcher.fetch_and_save_news()
        
        # Check how many AI sources failed by counting error messages in the file
        if digests_file and os.path.exists(digests_file):
            with open(digests_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Count the number of "❌ Failed to fetch news from this source" in the file
            failure_count = file_content.count("❌ Failed to fetch news from this source")
            ai_sources_succeeded = 3 - failure_count
            
            print(f"📊 AI sources succeeded: {ai_sources_succeeded}/3")
            print(f"📊 AI sources failed: {failure_count}/3")
        else:
            # If no digests file, assume all failed
            failure_count = 3
            ai_sources_succeeded = 0
            print("📊 No AI digests file found - assuming all sources failed")
        
        # Only use RSS feeds if 2+ AI sources failed
        use_rss_feeds = failure_count >= 2
        
        if use_rss_feeds:
            print("⚠️  Too many AI sources failed - will fetch RSS feeds as backup")
            # Step 1.5: Fetch RSS feeds as backup
            print("\n📡 Fetching RSS feeds as backup...")
            from scripts.pull_rss_feeds import get_all_rss_content
            rss_content = get_all_rss_content()
            
            # Save RSS feeds to separate file
            rss_file = "outputs/rss_feeds_summary.txt"
            with open(rss_file, 'w', encoding='utf-8') as f:
                f.write(f"RSS FEEDS SUMMARY FOR SOUTH AFRICAN PODCAST\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(rss_content)
            
            print(f"✅ RSS feeds saved to: {rss_file}")
        else:
            print("✅ Sufficient AI sources available - skipping RSS feeds")
            rss_file = None
        
        # Step 2: Generate transcript from available sources
        print("\n📝 Generating podcast transcript...")
        generator = TranscriptGenerator()
        
        if use_rss_feeds:
            # Use both AI news and RSS feeds (when AI sources are insufficient)
            print("Using AI news + RSS feeds for transcript generation")
            transcript_results = await generator.generate_transcript_from_multiple_sources(digests_file, rss_file)
        else:
            # Use only AI news (when we have sufficient AI sources)
            print("Using AI news only for transcript generation")
            transcript_results = await generator.generate_transcript_from_file(digests_file)
        
        if not transcript_results["success"]:
            return False, "", f"Failed to generate transcript: {transcript_results['error']}"
        
        # Validate transcript
        validation = transcript_results["validation"]
        if not validation["is_valid"]:
            print(f"⚠️  Warning: Transcript validation failed: {validation['errors']}")
        
        print(f"✅ AI content generation complete!")
        print(f"📊 News sources: {sum(1 for content in news_summaries.values() if content is not None)}/3 successful")
        print(f"📝 Transcript: {validation['word_count']} words")
        
        return True, transcript_results["saved_file"], ""
        
    except ImportError as e:
        return False, "", f"Missing AI modules: {e}"
    except Exception as e:
        return False, "", f"AI content generation failed: {e}"

def main():
    """
    Main function for podcast creation with support for both AI and RSS workflows.
    """
    print("🎙️  SA News Podcast Creator")
    print("=" * 50)
    
    # Check command line arguments for workflow selection
    use_ai_workflow = "--ai" in sys.argv or "-a" in sys.argv
    force_regenerate = "--force" in sys.argv or "-f" in sys.argv
    
    if use_ai_workflow:
        print("🤖 Using AI-powered workflow")
        transcript_file = run_ai_workflow()
        if not transcript_file:
            print("❌ AI workflow failed. Exiting.")
            return
    else:
        print("📰 Using existing transcript file")
        transcript_file = "outputs/latest_podcast_summary.txt"
        
        if not os.path.exists(transcript_file):
            print(f"❌ Transcript file {transcript_file} not found.")
            print("💡 Tip: Use --ai flag to generate content with AI workflow")
            return
            
        # Check if transcript is from today (unless force regenerate)
        if not force_regenerate:
            transcript_mtime = datetime.fromtimestamp(os.path.getmtime(transcript_file))
            current_date = datetime.now()
            if transcript_mtime.date() != current_date.date():
                print(f"⚠️  Transcript file is from {transcript_mtime.date()}, not today ({current_date.date()})")
                print("💡 Tip: Use --force flag to use existing transcript, or --ai to generate new content")
                return
        
        # Check if no transcript was generated
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_content = f.read()
            if transcript_content.strip() == "NO_TRANSCRIPT_GENERATED":
                print("❌ No transcript was generated for today.")
                print("💡 Tip: Use --ai flag to generate content with AI workflow")
                return
    
    print(f"\n🎵 Creating podcast from transcript: {transcript_file}")
    
    # Generate dated filename
    current_date = datetime.now().strftime('%Y-%m-%d')
    output_file = f"public/{current_date}.mp3"
    
    # Check if today's episode already exists
    if os.path.exists(output_file) and not force_regenerate:
        print(f"⚠️  Episode for {current_date} already exists at {output_file}")
        # In CI environment (GitHub Actions), always overwrite
        if os.getenv('GITHUB_ACTIONS'):
            print("🔄 Running in GitHub Actions - automatically overwriting existing file")
        else:
            user_input = input("Do you want to overwrite it? (y/n): ")
            if user_input.lower() != 'y':
                print("❌ Aborting podcast creation.")
                return
    
    # Force a file system sync to ensure we're reading the latest content
    os.sync()
    
    # Create the podcast
    print(f"\n🎬 Starting podcast creation...")
    if create_podcast_with_music(transcript_file, output_file):
        print(f"\n🎉 Podcast created successfully: {output_file}")
        print(f"📁 File size: {os.path.getsize(output_file) / (1024*1024):.1f} MB")
    else:
        print("❌ Failed to create podcast")

def run_ai_workflow():
    """
    Run the AI-powered workflow and return the transcript file path.
    
    Returns:
        str: Path to generated transcript file, or None if failed
    """
    try:
        # Run the async AI workflow
        success, transcript_file, error = asyncio.run(generate_ai_podcast_content())
        
        if success:
            return transcript_file
        else:
            print(f"❌ AI workflow failed: {error}")
            return None
            
    except Exception as e:
        print(f"❌ Error running AI workflow: {e}")
        return None

if __name__ == "__main__":
    main() 