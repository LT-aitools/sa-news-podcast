# ABOUTME: Integration tests for the complete podcast workflow
# ABOUTME: Tests both AI and RSS workflows end-to-end

import pytest
import asyncio
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import sys

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from podcast_creator import generate_ai_podcast_content, run_ai_workflow, main
from ai_news_fetcher import AINewsFetcher
from transcript_generator import TranscriptGenerator

class TestWorkflowIntegration:
    """Test cases for the complete podcast workflow integration."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock the secrets to avoid requiring actual API keys in tests
        self.mock_secrets = Mock()
        self.mock_secrets.get_perplexity_api_key.return_value = "test_perplexity_key"
        self.mock_secrets.get_claude_api_key.return_value = "test_claude_key"
        self.mock_secrets.get_openai_api_key.return_value = "test_openai_key"
    
    @pytest.mark.asyncio
    async def test_ai_workflow_success(self):
        """Test successful AI workflow execution."""
        # Mock successful AI news fetching
        mock_news_summaries = {
            "perplexity": "Test Perplexity news content",
            "claude": "Test Claude news content", 
            "chatgpt": "Test ChatGPT news content"
        }
        
        # Mock successful transcript generation
        mock_transcript = """**intro music**

Howzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah.

Today is Monday, January 15, 2024.

In today's news, there are several important developments.

**transition music**

In other news, the government has announced new policies.

**outro music**"""
        
        mock_validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "word_count": 50,
            "character_count": 300
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
                "transcript": mock_transcript,
                "saved_file": "test_transcript.txt",
                "validation": mock_validation
            }
            
            # Run the AI workflow
            success, transcript_file, error = await generate_ai_podcast_content()
            
            # Verify results
            assert success is True
            assert transcript_file == "test_transcript.txt"
            assert error == ""
            
            # Verify mocks were called
            mock_fetch.assert_called_once()
            mock_generate.assert_called_once_with("test_digests.txt")
    
    @pytest.mark.asyncio
    async def test_ai_workflow_news_fetch_failure(self):
        """Test AI workflow when news fetching fails."""
        with patch('ai_news_fetcher.get_secrets', return_value=self.mock_secrets), \
             patch('ai_news_fetcher.AINewsFetcher.fetch_and_save_news') as mock_fetch:
            
            # Mock news fetch failure
            mock_fetch.return_value = ({}, "")
            
            # Run the AI workflow
            success, transcript_file, error = await generate_ai_podcast_content()
            
            # Verify failure
            assert success is False
            assert transcript_file == ""
            assert "Failed to fetch AI news" in error
    
    @pytest.mark.asyncio
    async def test_ai_workflow_transcript_failure(self):
        """Test AI workflow when transcript generation fails."""
        mock_news_summaries = {
            "perplexity": "Test news content"
        }
        
        with patch('ai_news_fetcher.get_secrets', return_value=self.mock_secrets), \
             patch('transcript_generator.get_secrets', return_value=self.mock_secrets), \
             patch('ai_news_fetcher.AINewsFetcher.fetch_and_save_news') as mock_fetch, \
             patch('transcript_generator.TranscriptGenerator.generate_transcript_from_file') as mock_generate:
            
            # Set up mocks
            mock_fetch.return_value = (mock_news_summaries, "test_digests.txt")
            mock_generate.return_value = {
                "success": False,
                "error": "Claude API error",
                "transcript": None,
                "saved_file": "",
                "validation": None
            }
            
            # Run the AI workflow
            success, transcript_file, error = await generate_ai_podcast_content()
            
            # Verify failure
            assert success is False
            assert transcript_file == ""
            assert "Failed to generate transcript" in error
    
    def test_run_ai_workflow_success(self):
        """Test the run_ai_workflow function with successful execution."""
        with patch('podcast_creator.generate_ai_podcast_content') as mock_generate:
            mock_generate.return_value = (True, "test_transcript.txt", "")
            
            result = run_ai_workflow()
            
            assert result == "test_transcript.txt"
    
    def test_run_ai_workflow_failure(self):
        """Test the run_ai_workflow function with failure."""
        with patch('podcast_creator.generate_ai_podcast_content') as mock_generate:
            mock_generate.return_value = (False, "", "Test error")
            
            result = run_ai_workflow()
            
            assert result is None
    
    def test_main_function_ai_workflow(self):
        """Test main function with AI workflow flag."""
        # Mock the AI workflow
        with patch('podcast_creator.run_ai_workflow') as mock_run_ai, \
             patch('podcast_creator.create_podcast_with_music') as mock_create:
            
            # Set up mocks
            mock_run_ai.return_value = "test_transcript.txt"
            mock_create.return_value = True
            
            # Mock sys.argv to include --ai flag
            with patch('sys.argv', ['podcast_creator.py', '--ai']):
                # This should not raise an exception
                try:
                    main()
                except SystemExit:
                    pass  # Expected if the function calls sys.exit()
    
    def test_main_function_missing_transcript(self):
        """Test main function when transcript file is missing."""
        with patch('os.path.exists', return_value=False):
            with patch('sys.argv', ['podcast_creator.py']):
                # This should not raise an exception
                try:
                    main()
                except SystemExit:
                    pass  # Expected if the function calls sys.exit()
    
    def test_main_function_force_flag(self):
        """Test main function with force flag."""
        # Create a temporary transcript file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test transcript content")
            temp_file = f.name
        
        try:
            with patch('podcast_creator.create_podcast_with_music') as mock_create:
                mock_create.return_value = True
                
                # Mock sys.argv to include --force flag
                with patch('sys.argv', ['podcast_creator.py', '--force']), \
                     patch('podcast_creator.transcript_file', temp_file):
                    
                    # This should not raise an exception
                    try:
                        main()
                    except SystemExit:
                        pass  # Expected if the function calls sys.exit()
        
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    @pytest.mark.asyncio
    async def test_workflow_with_validation_warnings(self):
        """Test AI workflow with transcript validation warnings."""
        mock_news_summaries = {
            "perplexity": "Test news content"
        }
        
        mock_transcript = "Test transcript with some issues"
        mock_validation = {
            "is_valid": True,
            "errors": [],
            "warnings": ["Contains contraction: can't (will be expanded by sanitize_text)"],
            "word_count": 5,
            "character_count": 30
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
                "transcript": mock_transcript,
                "saved_file": "test_transcript.txt",
                "validation": mock_validation
            }
            
            # Run the AI workflow
            success, transcript_file, error = await generate_ai_podcast_content()
            
            # Verify results (should still succeed with warnings)
            assert success is True
            assert transcript_file == "test_transcript.txt"
            assert error == ""
    
    @pytest.mark.asyncio
    async def test_workflow_with_validation_errors(self):
        """Test AI workflow with transcript validation errors."""
        mock_news_summaries = {
            "perplexity": "Test news content"
        }
        
        mock_transcript = "Invalid transcript without required elements"
        mock_validation = {
            "is_valid": False,
            "errors": ["Missing required element: intro_music"],
            "warnings": [],
            "word_count": 5,
            "character_count": 50
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
                "transcript": mock_transcript,
                "saved_file": "test_transcript.txt",
                "validation": mock_validation
            }
            
            # Run the AI workflow
            success, transcript_file, error = await generate_ai_podcast_content()
            
            # Verify results (should still succeed but with validation errors)
            assert success is True
            assert transcript_file == "test_transcript.txt"
            assert error == ""

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
