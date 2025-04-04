import os
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import re
from pydub import AudioSegment
import tempfile
import requests
from datetime import datetime
import json

# Load environment variables
load_dotenv()

def filter_sound_effects(text):
    """
    Filter out sound effect references and speaker markers from the text
    
    Args:
        text (str): The input text
        
    Returns:
        str: Text with sound effects and speaker markers removed
    """
    # Pattern to match sound effect references in parentheses
    music_pattern = r'\([^)]*music[^)]*\)'
    
    # Pattern to match **Host:** markers (including the asterisks)
    host_pattern = r'\*\*Host:\*\*\s*'
    
    # Remove all sound effect references and host markers
    filtered_text = re.sub(music_pattern, '', text)
    filtered_text = re.sub(host_pattern, '', filtered_text)
    
    # Remove any remaining asterisks
    filtered_text = filtered_text.replace('*', '')
    
    # Remove any double spaces that might have been created
    filtered_text = re.sub(r'\s+', ' ', filtered_text)
    
    return filtered_text.strip()

def extract_sections(text):
    """
    Extract sections from the text based on sound effect markers
    
    Args:
        text (str): The input text
        
    Returns:
        list: List of tuples containing (text, music_type)
    """
    # Pattern to match sound effect references in parentheses
    music_pattern = r'\([^)]*music[^)]*\)'
    
    # Split the text while preserving the music markers
    parts = []
    last_end = 0
    
    for match in re.finditer(music_pattern, text):
        # Add the text before the music marker
        if match.start() > last_end:
            parts.append((text[last_end:match.start()].strip(), None))
        
        # Add the music marker
        music_text = match.group(0).lower()
        if "intro" in music_text:
            parts.append((None, "intro"))
        elif "outro" in music_text:
            parts.append((None, "outro"))
        elif "transition" in music_text:
            parts.append((None, "transition"))
        
        last_end = match.end()
    
    # Add any remaining text
    if last_end < len(text):
        parts.append((text[last_end:].strip(), None))
    
    # Clean up empty sections
    parts = [(text, music) for text, music in parts if text or music]
    
    return parts

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
    
    # If no output file specified, create a temporary one
    if output_file is None:
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        output_file = temp_file.name
        temp_file.close()
    
    try:
        # Configure speech synthesis
        speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key, 
            region=region
        )
        
        # Set the voice (using a South African English voice if available)
        speech_config.speech_synthesis_voice_name = "en-ZA-LeahNeural"
        
        # Set speech rate and style using SSML
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
               xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-ZA">
            <voice name="en-ZA-LeahNeural">
                <mstts:express-as style="newscast" styledegree="1.0">
                    <prosody rate="1.2">
                        {text}
                    </prosody>
                </mstts:express-as>
            </voice>
        </speak>
        """
        
        # Create audio output config
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
        
        # Create speech synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, 
            audio_config=audio_config
        )
        
        print(f"Converting text to speech...")
        
        # Synthesize speech using SSML
        result = synthesizer.speak_ssml_async(ssml).get()
        
        # Check result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print(f"Speech synthesis successful. Audio saved to {output_file}")
            return output_file
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")
            return None
    
    except Exception as e:
        print(f"Error during text-to-speech conversion: {e}")
        return None

def create_podcast_with_music(transcript_file, output_file="latest_podcast_audio.mp3"):
    """
    Create a podcast with text-to-speech and music in podcast-standard format
    
    Args:
        transcript_file (str): Path to the transcript file
        output_file (str): Path to save the final audio file
    """
    try:
        # Read the transcript file
        with open(transcript_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Extract sections from the text (before filtering sound effects)
        sections = extract_sections(text)
        
        if not sections:
            print("No sections found in the transcript.")
            return False
        
        # Load music files
        intro_music = AudioSegment.from_mp3("public/DvirSilver_intro.mp3")
        transition_music = AudioSegment.from_mp3("public/IvanLuzan_transition.mp3")
        outro_music = AudioSegment.from_mp3("public/DvirSilver_intro.mp3")
        
        # Reduce transition music volume to 50%
        transition_music = transition_music - 6  # -6 dB is approximately 50% volume
        
        # Create the podcast
        podcast = AudioSegment.empty()
        
        # Process each section
        for text, music_type in sections:
            if music_type == "intro":
                print("Adding intro music...")
                podcast += intro_music
            elif music_type == "transition":
                print("Adding transition music (at 50% volume)...")
                podcast += transition_music
            elif music_type == "outro":
                print("Adding outro music...")
                podcast += outro_music
            elif text:  # If there's text content
                # Filter the text to remove music markers and host markers
                filtered_text = filter_sound_effects(text)
                if filtered_text.strip():  # Only process if there's content after filtering
                    print("Converting text to speech...")
                    # Convert text to speech
                    section_audio_file = text_to_speech(filtered_text)
                    if section_audio_file:
                        section_audio = AudioSegment.from_wav(section_audio_file)
                        podcast += section_audio
        
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

def upload_to_redcircle(audio_file, title=None, description=None):
    """
    Upload the podcast episode to RedCircle
    
    Args:
        audio_file (str): Path to the audio file
        title (str, optional): Episode title. If None, uses current date
        description (str, optional): Episode description. If None, uses default
    """
    try:
        # Get RedCircle credentials from environment variables
        redcircle_api_key = os.getenv('REDCIRCLE_API_KEY')
        redcircle_podcast_id = os.getenv('REDCIRCLE_PODCAST_ID')
        
        if not redcircle_api_key or not redcircle_podcast_id:
            print("Error: RedCircle credentials not found in environment variables")
            return False
        
        # Set default title if none provided
        if title is None:
            # Format: "SA News for DD MON YYYY"
            current_date = datetime.now()
            title = f"SA News for {current_date.day} {current_date.strftime('%b')} {current_date.year}"
        
        # Set default description if none provided
        if description is None:
            description = "Your daily update on South African news, powered by AI."
        
        # Prepare the episode data
        episode_data = {
            "title": title,
            "description": description,
            "publishDate": datetime.now().isoformat(),
            "isDraft": False
        }
        
        # Upload the audio file
        files = {
            'audio': ('episode.mp3', open(audio_file, 'rb'), 'audio/mpeg')
        }
        
        headers = {
            'Authorization': f'Bearer {redcircle_api_key}',
            'Content-Type': 'multipart/form-data'
        }
        
        # Create the episode
        create_url = f"https://api.redcircle.fm/api/v1/podcasts/{redcircle_podcast_id}/episodes"
        create_response = requests.post(
            create_url,
            headers=headers,
            data={'episode': json.dumps(episode_data)},
            files=files
        )
        
        if create_response.status_code == 201:
            print(f"Successfully uploaded episode to RedCircle: {title}")
            return True
        else:
            print(f"Failed to upload episode: {create_response.text}")
            return False
            
    except Exception as e:
        print(f"Error uploading to RedCircle: {e}")
        return False

def main():
    # Get the transcript file
    transcript_file = "latest_podcast_summary.txt"
    
    if not os.path.exists(transcript_file):
        print(f"Transcript file {transcript_file} not found.")
        return
    
    print(f"Creating podcast from transcript: {transcript_file}")
    
    # Use a consistent filename for the audio output
    output_file = "latest_podcast_audio.mp3"  # Changed to .mp3
    
    # Delete the previous audio file if it exists
    if os.path.exists(output_file):
        try:
            os.remove(output_file)
            print(f"Deleted previous audio file: {output_file}")
        except Exception as e:
            print(f"Error deleting previous audio file: {e}")
    
    # Force a file system sync to ensure we're reading the latest content
    os.sync()
    
    # Create the podcast
    if create_podcast_with_music(transcript_file, output_file):
        print("Podcast created successfully.")
        
        # Uncomment to enable RedCircle upload
        # print("Uploading to RedCircle...")
        # upload_to_redcircle(output_file)
    else:
        print("Failed to create podcast")

if __name__ == "__main__":
    main() 