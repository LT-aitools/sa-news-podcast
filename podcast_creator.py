import os
import time
from dotenv import load_dotenv
import re
import tempfile
import requests
from datetime import datetime
import json
import html
import io
import wave

# Load environment variables
load_dotenv()

def sanitize_text(text):
    """
    Sanitize text for speech synthesis by removing special characters
    that might cause issues with the text-to-speech API
    
    Args:
        text (str): The input text
        
    Returns:
        str: Sanitized text
    """
    # Sanitize text for speech synthesis
    
    # Replace problematic characters, curly quotes with straight quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('—', '-').replace('–', '-')
    text = text.replace('…', '...')
    
    # Remove apostrophes to make contractions read as continuous words
    text = text.replace("'", "")
    
    # Replace emojis and other special characters
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
        if '**intro music**' in line_lower:
            if current_text:
                # Filter the accumulated text before adding
                clean_text = filter_sound_effects('\n'.join(current_text))
                if clean_text:
                    sections.append((clean_text, None))
                current_text = []
            sections.append((None, 'intro'))
        elif '**transition music**' in line_lower:
            if current_text:
                clean_text = filter_sound_effects('\n'.join(current_text))
                if clean_text:
                    sections.append((clean_text, None))
                current_text = []
            sections.append((None, 'transition'))
        elif '**outro music**' in line_lower:
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
    # Get Azure credentials from environment variables
    subscription_key = os.getenv('AZURE_SPEECH_KEY')
    region = os.getenv('AZURE_SPEECH_REGION')
    
    if not subscription_key:
        print("Error: AZURE_SPEECH_KEY not found in environment variables")
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
        
        # Create SSML with 1.2x speed
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-ZA">
            <voice name="en-ZA-LeahNeural">
                <prosody rate="1.2">
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

def main():
    # Get the transcript file
    transcript_file = "outputs/latest_podcast_summary.txt"
    
    if not os.path.exists(transcript_file):
        print(f"Transcript file {transcript_file} not found.")
        return
        
    # Check if transcript is from today
    transcript_mtime = datetime.fromtimestamp(os.path.getmtime(transcript_file))
    current_date = datetime.now()
    if transcript_mtime.date() != current_date.date():
        print(f"Warning: Transcript file is from {transcript_mtime.date()}, not today ({current_date.date()})")
        print("Please ensure the transcript is up to date before creating the podcast.")
        return
    
    # Check if no transcript was generated
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_content = f.read()
        if transcript_content.strip() == "NO_TRANSCRIPT_GENERATED":
            print("No transcript was generated for today. Skipping podcast creation.")
            return
    
    print(f"Creating podcast from transcript: {transcript_file}")
    
    # Generate dated filename
    current_date = current_date.strftime('%Y-%m-%d')
    output_file = f"public/{current_date}.mp3"
    
    # Check if today's episode already exists
    if os.path.exists(output_file):
        print(f"Warning: Episode for {current_date} already exists at {output_file}")
        # In CI environment (GitHub Actions), always overwrite
        if os.getenv('GITHUB_ACTIONS'):
            print("Running in GitHub Actions - automatically overwriting existing file")
        else:
            user_input = input("Do you want to overwrite it? (y/n): ")
            if user_input.lower() != 'y':
                print("Aborting podcast creation.")
                return
    
    # Force a file system sync to ensure we're reading the latest content
    os.sync()
    
    # Create the podcast
    if create_podcast_with_music(transcript_file, output_file):
        print("Podcast created successfully.")
    else:
        print("Failed to create podcast")

if __name__ == "__main__":
    main() 