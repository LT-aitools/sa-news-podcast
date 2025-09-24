# ABOUTME: Unit tests for Transcript Generator system
# ABOUTME: Tests Claude API integration and transcript validation

import asyncio
import pytest
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import pytz
from transcript_generator import TranscriptGenerator

class TestTranscriptGenerator:
    """Test cases for the Transcript Generator system."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock the secrets to avoid requiring actual API keys in tests
        self.mock_secrets = Mock()
        self.mock_secrets.get_claude_api_key.return_value = "test_claude_key"
        
        # Create generator instance with mocked secrets
        with patch('transcript_generator.get_secrets', return_value=self.mock_secrets):
            self.generator = TranscriptGenerator()
    
    def test_initialization(self):
        """Test that TranscriptGenerator initializes correctly."""
        assert self.generator is not None
        assert self.generator.transcript_prompt is not None
        assert "3-5 minute" in self.generator.transcript_prompt
        assert "Howzit South Africa" in self.generator.transcript_prompt
        assert "Mzansi Lowdown" in self.generator.transcript_prompt
        assert "I am your A.I. host, Leah" in self.generator.transcript_prompt
    
    def test_transcript_prompt_content(self):
        """Test that the transcript prompt contains all required elements."""
        prompt = self.generator.transcript_prompt
        
        # Check for key elements from NewWorkflow.md
        assert "3-5 minute (500-1000 words) daily news podcast transcript" in prompt
        assert "Use the news summaries in this TXT file for reference" in prompt
        assert "Do not make anything else up" in prompt
        assert "Focus on the key stories" in prompt
        assert "Howzit South Africa, and welcome to Mzansi Lowdown" in prompt
        assert "I am your A.I. host, Leah" in prompt
        assert "intro music" in prompt
        assert "outro music" in prompt
        assert "transition music" in prompt
        assert "cannot" in prompt and "can't" in prompt  # Example of contraction expansion
        assert "five hundred thousand rand" in prompt  # Example of number expansion
    
    def test_get_south_african_date(self):
        """Test South African date formatting."""
        date_str = self.generator.get_south_african_date()
        
        # Should be in format like "Monday, January 15, 2024"
        assert isinstance(date_str, str)
        assert len(date_str) > 10  # Should be a reasonable length
        assert "," in date_str  # Should contain commas for formatting
    
    def test_read_news_digests_file_success(self):
        """Test successful reading of news digests file."""
        test_content = "Test news digests content"
        test_file = "test_outputs/test_digests.txt"
        
        # Create test directory and file
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        
        try:
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            result = self.generator.read_news_digests_file(test_file)
            
            assert result == test_content
            
        finally:
            # Clean up test file
            if os.path.exists(test_file):
                os.remove(test_file)
            if os.path.exists("test_outputs"):
                os.rmdir("test_outputs")
    
    def test_read_news_digests_file_not_found(self):
        """Test handling of missing news digests file."""
        result = self.generator.read_news_digests_file("nonexistent_file.txt")
        assert result == ""
    
    @pytest.mark.asyncio
    async def test_generate_transcript_success(self):
        """Test successful transcript generation."""
        # Mock successful API response
        mock_response_data = {
            "content": [
                {
                    "text": "**intro music**\n\nHowzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah.\n\nToday is Monday, January 15, 2024.\n\nIn today's news...\n\n**transition music**\n\nIn other news...\n\n**outro music**"
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            test_news_content = "Test news content for transcript generation"
            result = await self.generator.generate_transcript(test_news_content)
            
            assert result is not None
            assert "Howzit South Africa" in result
            assert "intro music" in result
            assert "outro music" in result
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_transcript_failure(self):
        """Test transcript generation failure."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 401  # Unauthorized
            mock_response.text = AsyncMock(return_value="Unauthorized")
            mock_post.return_value.__aenter__.return_value = mock_response
            
            test_news_content = "Test news content"
            result = await self.generator.generate_transcript(test_news_content)
            
            assert result is None
    
    def test_validate_transcript_valid(self):
        """Test validation of a valid transcript."""
        valid_transcript = """**intro music**

Howzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah.

Today is Monday, January 15, 2024.

In today's news, there are several important developments across South Africa.

**transition music**

In other news, the government has announced new policies.

**outro music**"""
        
        validation = self.generator.validate_transcript(valid_transcript)
        
        assert validation["is_valid"] is True
        assert len(validation["errors"]) == 0
        assert validation["word_count"] > 0
        assert validation["character_count"] > 0
    
    def test_validate_transcript_missing_elements(self):
        """Test validation of transcript missing required elements."""
        invalid_transcript = "This is a transcript without the required elements."
        
        validation = self.generator.validate_transcript(invalid_transcript)
        
        assert validation["is_valid"] is False
        assert len(validation["errors"]) > 0
        assert any("Missing required element" in error for error in validation["errors"])
    
    def test_validate_transcript_contractions(self):
        """Test validation detects contractions."""
        transcript_with_contractions = """**intro music**

Howzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah.

Today is Monday, January 15, 2024.

In today's news, we can't ignore the developments.

**transition music**

In other news, they're working on new policies.

**outro music**"""
        
        validation = self.generator.validate_transcript(transcript_with_contractions)
        
        assert validation["is_valid"] is True  # Should still be valid
        assert len(validation["warnings"]) > 0
        assert any("Contains contraction" in warning for warning in validation["warnings"])
    
    def test_validate_transcript_word_count(self):
        """Test validation of word count."""
        # Create a very short transcript
        short_transcript = "**intro music**\n\nHowzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah.\n\n**outro music**"
        
        validation = self.generator.validate_transcript(short_transcript)
        
        assert validation["is_valid"] is True  # Should still be valid
        assert len(validation["warnings"]) > 0
        assert any("Transcript is short" in warning for warning in validation["warnings"])
    
    def test_save_transcript(self):
        """Test saving transcript to file."""
        test_transcript = "Test transcript content"
        test_output_file = "test_outputs/test_transcript.txt"
        
        # Ensure test directory exists
        os.makedirs(os.path.dirname(test_output_file), exist_ok=True)
        
        try:
            result = self.generator.save_transcript(test_transcript, test_output_file)
            
            assert result == test_output_file
            assert os.path.exists(test_output_file)
            
            # Check file content
            with open(test_output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert content == test_transcript
        
        finally:
            # Clean up test file
            if os.path.exists(test_output_file):
                os.remove(test_output_file)
            if os.path.exists("test_outputs"):
                os.rmdir("test_outputs")
    
    @pytest.mark.asyncio
    async def test_generate_transcript_from_file_integration(self):
        """Test the complete workflow from file to transcript."""
        # Create test news digests file
        test_digests_file = "test_outputs/test_digests.txt"
        test_output_file = "test_outputs/test_transcript.txt"
        test_news_content = "Test news digests content for transcript generation"
        
        os.makedirs(os.path.dirname(test_digests_file), exist_ok=True)
        
        try:
            # Write test news digests
            with open(test_digests_file, 'w', encoding='utf-8') as f:
                f.write(test_news_content)
            
            # Mock successful API response
            mock_response_data = {
                "content": [
                    {
                        "text": "**intro music**\n\nHowzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah.\n\nToday is Monday, January 15, 2024.\n\nIn today's news...\n\n**transition music**\n\nIn other news...\n\n**outro music**"
                    }
                ]
            }
            
            with patch('aiohttp.ClientSession.post') as mock_post:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value=mock_response_data)
                mock_post.return_value.__aenter__.return_value = mock_response
                
                results = await self.generator.generate_transcript_from_file(
                    test_digests_file, test_output_file
                )
                
                # Check results
                assert results["success"] is True
                assert results["error"] is None
                assert results["transcript"] is not None
                assert results["saved_file"] == test_output_file
                assert results["validation"] is not None
                assert results["validation"]["is_valid"] is True
                
                # Check that files were created
                assert os.path.exists(test_output_file)
                
        finally:
            # Clean up test files
            for file_path in [test_digests_file, test_output_file]:
                if os.path.exists(file_path):
                    os.remove(file_path)
            if os.path.exists("test_outputs"):
                os.rmdir("test_outputs")
    
    @pytest.mark.asyncio
    async def test_generate_transcript_from_file_missing_digests(self):
        """Test workflow with missing news digests file."""
        results = await self.generator.generate_transcript_from_file("nonexistent_file.txt")
        
        assert results["success"] is False
        assert "Failed to read news digests file" in results["error"]
        assert results["transcript"] is None
        assert results["saved_file"] == ""
        assert results["validation"] is None

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
