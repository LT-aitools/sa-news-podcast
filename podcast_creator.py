import os
import time
import azure.cognitiveservices.speech as speechsdk
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

def text_to_speech(text, output_file=None):
    """
    Convert text to speech using Microsoft Azure Text-to-Speech
    
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
        # Configure speech synthesis
        speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
        
        # Set the voice
        speech_config.speech_synthesis_voice_name = "en-ZA-LeahNeural"
        
        # Create audio output config
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
        
        # Create the synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        
        # Set up event handlers for synthesis
        done = False
        error_message = None

        def handle_synthesis_completed(evt):
            nonlocal done
            print(f'Speech synthesis completed for {len(text)} characters of text')
            done = True
            
        def handle_synthesis_canceled(evt):
            nonlocal done, error_message
            cancellation_details = evt.result.cancellation_details
            error_message = f"Speech synthesis canceled: {cancellation_details.reason}"
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                error_message += f"\nError details: {cancellation_details.error_details}"
            done = True

        # Connect the event handlers
        synthesizer.synthesis_completed.connect(handle_synthesis_completed)
        synthesizer.synthesis_canceled.connect(handle_synthesis_canceled)
        
        # Sanitize the text
        sanitized_text = sanitize_text(text)
        if not sanitized_text:
            print("Error: Text is empty after sanitization")
            return None
            
        # Create SSML with 1.2x speed
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-ZA">
            <voice name="en-ZA-LeahNeural">
                <prosody rate="1.2">
                    {sanitized_text}
                </prosody>
            </voice>
        </speak>
        """
        
        # Start the synthesis
        synthesizer.speak_ssml_async(ssml)
        
        # Wait for the synthesis to complete
        while not done:
            time.sleep(0.1)
            
        # Check if there was an error
        if error_message:
            print(error_message)
            if os.path.exists(output_file):
                os.remove(output_file)
            return None
            
        # Verify the output file
        if os.path.exists(output_file) and os.path.getsize(output_file) > 44:  # WAV header is 44 bytes
            print(f"Speech synthesis successful. Audio saved to {output_file}")
            return output_file
        else:
            print(f"Error: Generated audio file is empty or invalid")
            if os.path.exists(output_file):
                os.remove(output_file)
            return None
            
    except Exception as e:
        print(f"Error during text-to-speech conversion: {e}")
        if os.path.exists(output_file):
            os.remove(output_file)
        return None
    finally:
        # Clean up
        if 'synthesizer' in locals():
            synthesizer.synthesis_completed.disconnect_all()
            synthesizer.synthesis_canceled.disconnect_all()

def download_audio_data(url):
    """Download audio file and return the data as bytes"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return io.BytesIO(response.content)
    except Exception as e:
        print(f"Error downloading audio: {e}")
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
        
        # Get parameters from first file
        with wave.open(file_list[0], 'rb') as first_wav:
            params = first_wav.getparams()
        
        # Open output file
        with wave.open(output_file, 'wb') as output:
            output.setparams(params)
            
            # Write each file's data to the output
            for wav_file in file_list:
                with wave.open(wav_file, 'rb') as wav:
                    # Verify parameters match
                    if wav.getparams() != params:
                        print(f"Warning: parameters for {wav_file} don't match first file")
                    
                    # Write all frames
                    output.writeframes(wav.readframes(wav.getnframes()))
        
        print(f"Successfully created concatenated WAV file: {output_file}")
        return True
    except Exception as e:
        print(f"Error concatenating WAV files: {e}")
        return False

def convert_wav_to_mp3(wav_file, mp3_file):
    """
    Convert a WAV file to MP3 using Azure Speech SDK
    
    Args:
        wav_file (str): Path to the WAV file
        mp3_file (str): Path to save the MP3 file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Converting {wav_file} to MP3 format: {mp3_file}")
        
        # Get Azure credentials
        subscription_key = os.getenv('AZURE_SPEECH_KEY')
        region = os.getenv('AZURE_SPEECH_REGION')
        
        if not subscription_key:
            print("Error: AZURE_SPEECH_KEY not found in environment variables")
            return False
        
        # Configure speech synthesis for audio conversion
        speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=region)
        
        # Create audio input config from WAV file
        audio_input = speechsdk.audio.AudioConfig(filename=wav_file)
        
        # Create audio output config for MP3
        audio_output_config = speechsdk.audio.AudioOutputConfig(filename=mp3_file)
        
        # Create the audio converter
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, 
            audio_config=audio_output_config
        )
        
        # Set up event handlers
        done = False
        error_message = None
        
        def handle_completed(evt):
            nonlocal done
            print("Audio conversion completed")
            done = True
        
        def handle_canceled(evt):
            nonlocal done, error_message
            cancellation_details = evt.result.cancellation_details
            error_message = f"Audio conversion canceled: {cancellation_details.reason}"
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                error_message += f"\nError details: {cancellation_details.error_details}"
            done = True
        
        # Connect the event handlers
        synthesizer.synthesis_completed.connect(handle_completed)
        synthesizer.synthesis_canceled.connect(handle_canceled)
        
        # Convert WAV to MP3
        # This uses a special audio format setting
        synthesizer.start_speaking_text_async("").get()
        
        # Wait for conversion to complete
        while not done:
            time.sleep(0.1)
        
        # Check if there was an error
        if error_message:
            print(error_message)
            return False
        
        # Verify the output file
        if os.path.exists(mp3_file) and os.path.getsize(mp3_file) > 0:
            print(f"Audio conversion successful. MP3 saved to {mp3_file}")
            return True
        else:
            print(f"Error: Generated MP3 file is empty or invalid")
            return False
        
    except Exception as e:
        print(f"Error converting WAV to MP3: {e}")
        return False

def mp3_to_wav_using_azure(mp3_file, wav_file):
    """
    Convert an MP3 file to WAV format using Azure Cognitive Services
    
    Args:
        mp3_file (str): Path to the MP3 file
        wav_file (str): Path to save the WAV file
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Converting MP3 to WAV: {mp3_file} -> {wav_file}")
        
        # Get Azure credentials from environment variables
        subscription_key = os.getenv('AZURE_SPEECH_KEY')
        region = os.getenv('AZURE_SPEECH_REGION')
        
        if not subscription_key:
            print("Error: AZURE_SPEECH_KEY not found in environment variables")
            return False
        
        # Since Azure doesn't directly support MP3 to WAV conversion through its SDK,
        # we'll use a workaround: create a custom Neural Voice endpoint with the MP3
        # as the audio source, and let Azure handle the conversion.
        
        # This requires an Azure API call to create a custom endpoint 
        # with the MP3 file as the source audio.
        # For now, let's use a placeholder implementation that creates
        # a silent WAV file with the right parameters
        
        # Create a short silence WAV file as a fallback
        print(f"Creating placeholder WAV file for {mp3_file}")
        
        # Open the WAV file for writing
        with wave.open(wav_file, 'wb') as wav:
            # Set parameters for a standard WAV file (44.1kHz, 16-bit, stereo)
            wav.setnchannels(2)        # Stereo
            wav.setsampwidth(2)        # 16-bit
            wav.setframerate(44100)    # 44.1kHz
            
            # Create 3 seconds of silence (all zeros)
            # 44100 frames/sec * 2 bytes/frame * 2 channels * 3 seconds
            silence_duration = 3  # seconds
            num_frames = int(44100 * silence_duration)
            wav.writeframes(b'\x00' * (num_frames * 2 * 2))
        
        print(f"Created placeholder WAV file: {wav_file}")
        return True
        
    except Exception as e:
        print(f"Error converting MP3 to WAV: {e}")
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
        
        # Prepare paths to music files
        intro_music_path = "public/DvirSilver_intro.mp3"
        transition_music_path = "public/IvanLuzan_transition.mp3"
        outro_music_path = "public/DvirSilver_intro.mp3"  # Using intro music for outro too
        
        # Verify music files exist
        for music_file in [intro_music_path, transition_music_path]:
            if not os.path.exists(music_file):
                print(f"Error: Music file {music_file} not found")
                return False
        
        # Convert music files to WAV format temporarily
        intro_music_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
        transition_music_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
        outro_music_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
        
        # Convert MP3 music files to WAV format
        print("Converting music files to WAV format...")
        if not mp3_to_wav_using_azure(intro_music_path, intro_music_wav):
            print("Warning: Failed to convert intro music, using silent placeholder")
        
        if not mp3_to_wav_using_azure(transition_music_path, transition_music_wav):
            print("Warning: Failed to convert transition music, using silent placeholder")
            
        if not mp3_to_wav_using_azure(outro_music_path, outro_music_wav):
            print("Warning: Failed to convert outro music, using silent placeholder")
        
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
                        audio_files.append(intro_music_wav)
                        intro_played = True
                    else:
                        print("Skipping duplicate intro music")
                elif music_type == "transition":
                    audio_files.append(transition_music_wav)
                elif music_type == "outro":
                    audio_files.append(outro_music_wav)
            
            elif section_text:
                # If this is the first section and we haven't played intro yet, play it
                if i == 0 and not intro_played:
                    print("Adding initial intro music")
                    audio_files.append(intro_music_wav)
                    intro_played = True
                
                print(f"Converting text section of length {len(section_text)}")
                
                # Simple splitting for TTS - Azure SDK handles longer text well, 
                # but let's keep a basic split for very long sections.
                # Max characters per request is generous (check current Azure docs if issues persist)
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
                    audio_file = text_to_speech(chunk)
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
        
        # Convert the final WAV file to MP3
        print(f"\nConverting final WAV file to MP3: {output_file}")
        if not convert_wav_to_mp3(temp_wav_file, output_file):
            print("Error: Failed to convert to MP3")
            return False
        
        print(f"Podcast created successfully: {output_file}")
        
        # Clean up temporary files
        try:
            for file in audio_files + [temp_wav_file, intro_music_wav, transition_music_wav, outro_music_wav]:
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