# ABOUTME: Azure Speech SDK test script for SA News Podcast
# ABOUTME: Simple text-to-speech testing using Azure Cognitive Services

import azure.cognitiveservices.speech as speechsdk
from secure_secrets import get_secrets

# Load Azure Speech credentials from secure secrets
try:
    secrets = get_secrets()
    speech_key = secrets.get_azure_speech_key()
    speech_region = secrets.get_azure_speech_region()
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
except Exception as e:
    print(f"Error: Failed to load Azure Speech credentials: {e}")
    exit(1)
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

# The neural multilingual voice can speak different languages based on the input text.
speech_config.speech_synthesis_voice_name='en-ZA-LeahNeural'

speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

# Get text from the console and synthesize to the default speaker.
print("Enter some text that you want to speak >")
text = input()

speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()

if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("Speech synthesized for text [{}]".format(text))
elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
    cancellation_details = speech_synthesis_result.cancellation_details
    print("Speech synthesis canceled: {}".format(cancellation_details.reason))
    if cancellation_details.reason == speechsdk.CancellationReason.Error:
        if cancellation_details.error_details:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")