import os
import time
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import re
from pydub import AudioSegment
import tempfile
import requests
from datetime import datetime
import json
import html

# Load environment variables
load_dotenv()

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
        # Check for exact music marker matches
        if '**Intro music**' in line:
            if current_text:
                # Filter the accumulated text before adding
                clean_text = filter_sound_effects('\n'.join(current_text))
                if clean_text:
                    sections.append((clean_text, None))
                current_text = []
            sections.append((None, 'intro'))
        elif '**Transition music**' in line:
            if current_text:
                clean_text = filter_sound_effects('\n'.join(current_text))
                if clean_text:
                    sections.append((clean_text, None))
                current_text = []
            sections.append((None, 'transition'))
        elif '**Outro music**' in line:
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

def sanitize_text(text):
    """
    Sanitize text for SSML by:
    1. Converting HTML entities
    2. Escaping special characters
    3. Removing problematic characters
    """
    # Convert HTML entities to characters
    text = html.unescape(text)
    
    # Escape special characters for SSML
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    
    # Remove any other problematic characters
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    
    # Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

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
    region = os.getenv('AZURE_SPEECH_REGION', 'eastus')
    
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
        print("Initializing Azure Speech SDK...")
        speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key, 
            region=region
        )
        print("Speech config created successfully")
        
        # Set the voice (using a South African English voice if available)
        print(f"Setting voice to en-ZA-LeahNeural...")
        speech_config.speech_synthesis_voice_name = "en-ZA-LeahNeural"
        print("Voice set successfully")
        
        # Sanitize the text
        sanitized_text = sanitize_text(text)
        
        # Log the text being processed
        print(f"\nProcessing text chunk (first 100 chars): {sanitized_text[:100]}...")
        
        if not sanitized_text:
            print("Error: Text is empty after sanitization")
            return None
            
        # Set speech rate and style using SSML
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
               xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-ZA">
            <voice name="en-ZA-LeahNeural">
                <mstts:express-as style="newscast" styledegree="1.0">
                    <prosody rate="1.2">
                        {sanitized_text}
                    </prosody>
                </mstts:express-as>
            </voice>
        </speak>
        """
        
        print("Creating audio output config...")
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
        print("Audio config created successfully")
        
        print("Creating speech synthesizer...")
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, 
            audio_config=audio_config
        )
        print("Speech synthesizer created successfully")
        
        print("Starting speech synthesis...")
        result = synthesizer.speak_ssml_async(ssml).get()
        print(f"Speech synthesis completed with reason: {result.reason}")
        
        # Check result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # Verify the output file exists and is not empty
            if os.path.exists(output_file) and os.path.getsize(output_file) > 44:  # WAV header is 44 bytes
                print(f"Speech synthesis successful. Audio saved to {output_file}")
                return output_file
            else:
                print(f"Error: Generated audio file is empty or invalid")
                if os.path.exists(output_file):
                    os.remove(output_file)
                return None
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")
                print(f"Problematic text chunk: {text}")
                print(f"Sanitized text: {sanitized_text}")
            if os.path.exists(output_file):
                os.remove(output_file)
            return None
    
    except Exception as e:
        print(f"Error during text-to-speech conversion: {e}")
        if os.path.exists(output_file):
            os.remove(output_file)
        return None

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
        
        # Read the transcript file
        with open(transcript_file, 'r', encoding='utf-8') as f:
            text = f.read()
            print(f"\nRead transcript file: {len(text)} characters")
        
        # Extract sections with music markers
        sections = extract_sections(text)
        print(f"Extracted {len(sections)} sections")
        
        # Initialize audio
        podcast = AudioSegment.empty()
        
        # Load music files
        try:
            intro_music = AudioSegment.from_mp3("public/DvirSilver_intro.mp3")
            transition_music = AudioSegment.from_mp3("public/IvanLuzan_transition.mp3")
            outro_music = AudioSegment.from_mp3("public/DvirSilver_intro.mp3")
            print("Successfully loaded all music files")
        except Exception as e:
            print(f"Error loading music files: {e}")
            return False
        
        # Process each section
        intro_played = False  # Track if we've played the intro
        for i, (section_text, music_type) in enumerate(sections):
            print(f"\nProcessing section {i+1}/{len(sections)}")
            if music_type:
                print(f"Adding {music_type} music")
                # Add appropriate music
                if music_type == "intro":
                    if not intro_played:  # Only play intro once
                        podcast += intro_music
                        intro_played = True
                    else:
                        print("Skipping duplicate intro music")
                elif music_type == "transition":
                    podcast += transition_music
                elif music_type == "outro":
                    podcast += outro_music
            elif section_text:
                # If this is the first section and we haven't played intro yet, play it
                if i == 0 and not intro_played:
                    print("Adding initial intro music")
                    podcast += intro_music
                    intro_played = True
                
                print(f"Converting text section of length {len(section_text)}")
                # Convert text to speech
                # Split text into smaller chunks to avoid TTS limits
                chunks = re.split(r'(?<=[.!?])\s+', filter_sound_effects(section_text))
                print(f"Split into {len(chunks)} chunks")
                current_chunk = ""
                
                for j, chunk in enumerate(chunks):
                    if len(current_chunk) + len(chunk) < 1000:
                        current_chunk += " " + chunk
                    else:
                        if current_chunk:
                            print(f"\nProcessing chunk {j}/{len(chunks)}")
                            audio_file = text_to_speech(current_chunk)
                            if audio_file:
                                try:
                                    audio_segment = AudioSegment.from_wav(audio_file)
                                    if len(audio_segment) > 0:  # Check if audio segment is not empty
                                        podcast += audio_segment
                                    else:
                                        print("Warning: Empty audio segment generated")
                                except Exception as e:
                                    print(f"Error processing audio file: {e}")
                            else:
                                print("Warning: Failed to generate audio for chunk")
                        current_chunk = chunk
                
                # Don't forget the last chunk
                if current_chunk:
                    print(f"\nProcessing final chunk")
                    audio_file = text_to_speech(current_chunk)
                    if audio_file:
                        try:
                            audio_segment = AudioSegment.from_wav(audio_file)
                            if len(audio_segment) > 0:
                                podcast += audio_segment
                            else:
                                print("Warning: Empty audio segment generated for final chunk")
                        except Exception as e:
                            print(f"Error processing final audio file: {e}")
        
        # Check if we have any audio content
        if len(podcast) == 0:
            print("Error: No audio content was generated")
            return False
            
        print(f"\nExporting final podcast (length: {len(podcast)}ms)")
        # Export the final podcast in podcast-standard format
        podcast.export(
            output_file,
            format="mp3",
            parameters=[
                "-ar", "44100",  # Sample rate: 44.1 kHz
                "-ac", "2",      # Channels: Stereo
                "-b:a", "128k"   # Bitrate: 128 kbps
            ]
        )
        print(f"Podcast created successfully: {output_file}")
        
        # Clean up temporary files
        for file in os.listdir(tempfile.gettempdir()):
            if file.endswith('.wav') and file.startswith('tmp'):
                try:
                    os.remove(os.path.join(tempfile.gettempdir(), file))
                except:
                    pass
        
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
    
    print(f"Creating podcast from transcript: {transcript_file}")
    
    # Generate dated filename
    current_date = datetime.now().strftime('%Y-%m-%d')
    output_file = f"public/{current_date}.mp3"
    
    # Check if today's episode already exists
    if os.path.exists(output_file):
        print(f"Warning: Episode for {current_date} already exists at {output_file}")
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