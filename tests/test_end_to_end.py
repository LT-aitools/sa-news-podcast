# ABOUTME: End-to-end tests for complete podcast generation workflow
# ABOUTME: Tests the full pipeline from AI news fetching to final MP3 output

import pytest
import asyncio
import os
import tempfile
import sys
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from podcast_creator import main, create_podcast_with_music
from ai_news_fetcher import AINewsFetcher
from transcript_generator import TranscriptGenerator

class TestEndToEnd:
    """End-to-end tests for the complete podcast generation workflow."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock the secrets to avoid requiring actual API keys in tests
        self.mock_secrets = Mock()
        self.mock_secrets.get_perplexity_api_key.return_value = "test_perplexity_key"
        self.mock_secrets.get_claude_api_key.return_value = "test_claude_key"
        self.mock_secrets.get_openai_api_key.return_value = "test_openai_key"
        self.mock_secrets.get_azure_speech_key.return_value = "test_azure_key"
        self.mock_secrets.get_azure_speech_region.return_value = "test_region"
    
    def create_test_transcript(self):
        """Create a test transcript file with proper format."""
        test_transcript = """**intro music**

Howzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah.

Today is Monday, January 15, 2024.

In today's news, there are several important developments across South Africa. The government has announced new policies to address economic challenges.

**transition music**

In other news, the country's infrastructure projects are progressing well. New developments in renewable energy are showing positive results.

**transition music**

Finally, local communities are coming together to address social issues. These grassroots initiatives are making a real difference.

**outro music**"""
        
        return test_transcript
    
    @pytest.mark.asyncio
    async def test_complete_ai_workflow_simulation(self):
        """Test the complete AI workflow from news fetching to transcript generation."""
        # Mock successful AI news fetching
        mock_news_summaries = {
            "perplexity": "Test Perplexity news content about South Africa",
            "claude": "Test Claude news content about South Africa", 
            "chatgpt": "Test ChatGPT news content about South Africa"
        }
        
        # Mock successful transcript generation
        test_transcript = self.create_test_transcript()
        mock_validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "word_count": 100,
            "character_count": 600
        }
        
        with patch('ai_news_fetcher.get_secrets', return_value=self.mock_secrets), \
             patch('transcript_generator.get_secrets', return_value=self.mock_secrets), \
             patch('ai_news_fetcher.AINewsFetcher.fetch_and_save_news') as mock_fetch, \
             patch('transcript_generator.TranscriptGenerator.generate_transcript_from_file') as mock_generate:
            
            # Set up mocks
            mock_fetch.return_value = (mock_news_summaries, "test_digests.txt")
            mock_generate.return_value = {
                "success": True,
                "error": None,
                "transcript": test_transcript,
                "saved_file": "test_transcript.txt",
                "validation": mock_validation
            }
            
            # Test the complete AI workflow
            from podcast_creator import generate_ai_podcast_content
            success, transcript_file, error = await generate_ai_podcast_content()
            
            # Verify the complete workflow
            assert success is True
            assert transcript_file == "test_transcript.txt"
            assert error == ""
            
            # Verify all components were called
            mock_fetch.assert_called_once()
            mock_generate.assert_called_once_with("test_digests.txt")
    
    def test_podcast_creation_with_mock_tts(self):
        """Test podcast creation with mocked TTS to avoid actual API calls."""
        test_transcript = self.create_test_transcript()
        
        # Create a temporary transcript file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(test_transcript)
            transcript_file = f.name
        
        try:
            # Mock the TTS function to avoid actual API calls
            with patch('podcast_creator.text_to_speech_rest') as mock_tts, \
                 patch('podcast_creator.concatenate_wav_files') as mock_concat, \
                 patch('podcast_creator.convert_audio_ffmpeg') as mock_convert:
                
                # Set up mocks
                mock_tts.return_value = "test_audio.wav"
                mock_concat.return_value = True
                mock_convert.return_value = True
                
                # Create a temporary output file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                    output_file = f.name
                
                try:
                    # Test podcast creation
                    result = create_podcast_with_music(transcript_file, output_file)
                    
                    # Verify the result
                    assert result is True
                    
                    # Verify TTS was called for text sections
                    assert mock_tts.called
                    
                    # Verify concatenation was called
                    mock_concat.assert_called_once()
                    
                    # Verify conversion was called
                    mock_convert.assert_called_once()
                
                finally:
                    # Clean up output file
                    if os.path.exists(output_file):
                        os.remove(output_file)
        
        finally:
            # Clean up transcript file
            if os.path.exists(transcript_file):
                os.remove(transcript_file)
    
    def test_main_function_ai_workflow_complete(self):
        """Test the main function with AI workflow flag."""
        test_transcript = self.create_test_transcript()
        
        # Create a temporary transcript file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(test_transcript)
            transcript_file = f.name
        
        try:
            # Mock all the components
            with patch('podcast_creator.run_ai_workflow') as mock_run_ai, \
                 patch('podcast_creator.create_podcast_with_music') as mock_create, \
                 patch('os.path.exists') as mock_exists, \
                 patch('os.getsize') as mock_size:
                
                # Set up mocks
                mock_run_ai.return_value = transcript_file
                mock_create.return_value = True
                mock_exists.return_value = False  # No existing episode
                mock_size.return_value = 1024 * 1024  # 1MB file size
                
                # Mock sys.argv to include --ai flag
                with patch('sys.argv', ['podcast_creator.py', '--ai']):
                    # This should not raise an exception
                    try:
                        main()
                    except SystemExit:
                        pass  # Expected if the function calls sys.exit()
                    
                    # Verify the AI workflow was called
                    mock_run_ai.assert_called_once()
                    
                    # Verify podcast creation was called
                    mock_create.assert_called_once()
        
        finally:
            # Clean up transcript file
            if os.path.exists(transcript_file):
                os.remove(transcript_file)
    
    def test_error_handling_throughout_workflow(self):
        """Test error handling at various points in the workflow."""
        # Test 1: AI workflow failure
        with patch('podcast_creator.run_ai_workflow') as mock_run_ai:
            mock_run_ai.return_value = None  # Simulate failure
            
            with patch('sys.argv', ['podcast_creator.py', '--ai']):
                try:
                    main()
                except SystemExit:
                    pass  # Expected
                
                mock_run_ai.assert_called_once()
        
        # Test 2: Podcast creation failure
        test_transcript = self.create_test_transcript()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(test_transcript)
            transcript_file = f.name
        
        try:
            with patch('podcast_creator.create_podcast_with_music') as mock_create:
                mock_create.return_value = False  # Simulate failure
                
                with patch('sys.argv', ['podcast_creator.py', '--ai']), \
                     patch('podcast_creator.run_ai_workflow') as mock_run_ai:
                    
                    mock_run_ai.return_value = transcript_file
                    
                    try:
                        main()
                    except SystemExit:
                        pass  # Expected
                    
                    mock_create.assert_called_once()
        
        finally:
            if os.path.exists(transcript_file):
                os.remove(transcript_file)
    
    def test_file_validation_and_cleanup(self):
        """Test file validation and cleanup throughout the workflow."""
        # Test with invalid transcript content
        invalid_transcript = "This is not a valid podcast transcript"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(invalid_transcript)
            transcript_file = f.name
        
        try:
            # Mock the TTS function
            with patch('podcast_creator.text_to_speech_rest') as mock_tts, \
                 patch('podcast_creator.concatenate_wav_files') as mock_concat, \
                 patch('podcast_creator.convert_audio_ffmpeg') as mock_convert:
                
                mock_tts.return_value = "test_audio.wav"
                mock_concat.return_value = True
                mock_convert.return_value = True
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                    output_file = f.name
                
                try:
                    # Test that the workflow handles invalid content gracefully
                    result = create_podcast_with_music(transcript_file, output_file)
                    
                    # Should still attempt to process (TTS will handle the content)
                    assert result is True
                
                finally:
                    if os.path.exists(output_file):
                        os.remove(output_file)
        
        finally:
            if os.path.exists(transcript_file):
                os.remove(transcript_file)
    
    def test_workflow_with_different_transcript_formats(self):
        """Test workflow with different transcript formats and edge cases."""
        test_cases = [
            # Minimal valid transcript
            """**intro music**
Howzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah.
**outro music**""",
            
            # Transcript with multiple transitions
            """**intro music**
Howzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah.
**transition music**
Story one.
**transition music**
Story two.
**transition music**
Story three.
**outro music**""",
            
            # Transcript with special characters (should be handled by sanitize_text)
            """**intro music**
Howzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah.
The government can't solve the country's problems.
**outro music**"""
        ]
        
        for i, test_transcript in enumerate(test_cases):
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(test_transcript)
                transcript_file = f.name
            
            try:
                with patch('podcast_creator.text_to_speech_rest') as mock_tts, \
                     patch('podcast_creator.concatenate_wav_files') as mock_concat, \
                     patch('podcast_creator.convert_audio_ffmpeg') as mock_convert:
                    
                    mock_tts.return_value = "test_audio.wav"
                    mock_concat.return_value = True
                    mock_convert.return_value = True
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                        output_file = f.name
                    
                    try:
                        result = create_podcast_with_music(transcript_file, output_file)
                        assert result is True, f"Test case {i+1} failed"
                    
                    finally:
                        if os.path.exists(output_file):
                            os.remove(output_file)
            
            finally:
                if os.path.exists(transcript_file):
                    os.remove(transcript_file)

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
