# ABOUTME: Unit tests for AI News Fetcher system
# ABOUTME: Tests all AI API integrations and error handling

import asyncio
import pytest
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from ai_news_fetcher import AINewsFetcher

class TestAINewsFetcher:
    """Test cases for the AI News Fetcher system."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Mock the secrets to avoid requiring actual API keys in tests
        self.mock_secrets = Mock()
        self.mock_secrets.get_perplexity_api_key.return_value = "test_perplexity_key"
        self.mock_secrets.get_claude_api_key.return_value = "test_claude_key"
        self.mock_secrets.get_openai_api_key.return_value = "test_openai_key"
        
        # Create fetcher instance with mocked secrets
        with patch('ai_news_fetcher.get_secrets', return_value=self.mock_secrets):
            self.fetcher = AINewsFetcher()
    
    def test_initialization(self):
        """Test that AINewsFetcher initializes correctly."""
        assert self.fetcher is not None
        assert self.fetcher.web_search_prompt is not None
        assert "South African news stories" in self.fetcher.web_search_prompt
        assert "Breaking national and regional news" in self.fetcher.web_search_prompt
    
    def test_web_search_prompt_content(self):
        """Test that the web search prompt contains all required elements."""
        prompt = self.fetcher.web_search_prompt
        
        # Check for key elements from NewWorkflow.md
        assert "most important and widely-discussed South African news stories" in prompt
        assert "Breaking national and regional news and major developments" in prompt
        assert "Viral stories getting significant attention" in prompt
        assert "Notable events affecting many people" in prompt
        assert "Surprising or unusual stories gaining traction" in prompt
        assert "Ignore purely international stories that don't involve South Africa" in prompt
    
    @pytest.mark.asyncio
    async def test_fetch_perplexity_news_success(self):
        """Test successful Perplexity API fetch."""
        # Mock successful API response
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": "Test Perplexity news content about South Africa"
                    }
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await self.fetcher.fetch_perplexity_news()
            
            assert result == "Test Perplexity news content about South Africa"
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_perplexity_news_failure(self):
        """Test Perplexity API fetch failure."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 401  # Unauthorized
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await self.fetcher.fetch_perplexity_news()
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_fetch_claude_news_success(self):
        """Test successful Claude API fetch."""
        # Mock successful API response
        mock_response_data = {
            "content": [
                {
                    "text": "Test Claude news content about South Africa"
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await self.fetcher.fetch_claude_news()
            
            assert result == "Test Claude news content about South Africa"
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_claude_news_failure(self):
        """Test Claude API fetch failure."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 429  # Rate limited
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await self.fetcher.fetch_claude_news()
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_fetch_chatgpt_news_success(self):
        """Test successful ChatGPT API fetch."""
        # Mock successful API response
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": "Test ChatGPT news content about South Africa"
                    }
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await self.fetcher.fetch_chatgpt_news()
            
            assert result == "Test ChatGPT news content about South Africa"
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_chatgpt_news_failure(self):
        """Test ChatGPT API fetch failure."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 500  # Server error
            mock_post.return_value.__aenter__.return_value = mock_response
            
            result = await self.fetcher.fetch_chatgpt_news()
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_fetch_all_news_concurrent(self):
        """Test that all news sources are fetched concurrently."""
        # Mock all three APIs to return different content
        mock_responses = {
            "perplexity": {"choices": [{"message": {"content": "Perplexity news"}}]},
            "claude": {"content": [{"text": "Claude news"}]},
            "chatgpt": {"choices": [{"message": {"content": "ChatGPT news"}}]}
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Set up mock responses
            mock_response = AsyncMock()
            mock_response.status = 200
            
            def mock_json():
                # Return different content based on call count
                call_count = mock_post.call_count
                if call_count == 1:
                    return mock_responses["perplexity"]
                elif call_count == 2:
                    return mock_responses["claude"]
                else:
                    return mock_responses["chatgpt"]
            
            mock_response.json = AsyncMock(side_effect=mock_json)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            results = await self.fetcher.fetch_all_news()
            
            assert results["perplexity"] == "Perplexity news"
            assert results["claude"] == "Claude news"
            assert results["chatgpt"] == "ChatGPT news"
            assert mock_post.call_count == 3
    
    def test_save_news_digests(self):
        """Test saving news digests to file."""
        test_summaries = {
            "perplexity": "Test Perplexity content",
            "claude": "Test Claude content",
            "chatgpt": "Test ChatGPT content"
        }
        
        test_output_file = "test_outputs/test_digests.txt"
        
        # Ensure test directory exists
        os.makedirs(os.path.dirname(test_output_file), exist_ok=True)
        
        try:
            result = self.fetcher.save_news_digests(test_summaries, test_output_file)
            
            assert result == test_output_file
            assert os.path.exists(test_output_file)
            
            # Check file content
            with open(test_output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "AI NEWS DIGESTS FOR SOUTH AFRICAN PODCAST" in content
                assert "Test Perplexity content" in content
                assert "Test Claude content" in content
                assert "Test ChatGPT content" in content
                assert "PERPLEXITY NEWS DIGEST" in content
                assert "CLAUDE NEWS DIGEST" in content
                assert "CHATGPT NEWS DIGEST" in content
        
        finally:
            # Clean up test file
            if os.path.exists(test_output_file):
                os.remove(test_output_file)
            if os.path.exists("test_outputs"):
                os.rmdir("test_outputs")
    
    def test_save_news_digests_with_none_values(self):
        """Test saving news digests when some sources fail."""
        test_summaries = {
            "perplexity": "Test Perplexity content",
            "claude": None,  # Failed fetch
            "chatgpt": "Test ChatGPT content"
        }
        
        test_output_file = "test_outputs/test_digests_with_none.txt"
        
        # Ensure test directory exists
        os.makedirs(os.path.dirname(test_output_file), exist_ok=True)
        
        try:
            result = self.fetcher.save_news_digests(test_summaries, test_output_file)
            
            assert result == test_output_file
            assert os.path.exists(test_output_file)
            
            # Check file content
            with open(test_output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Test Perplexity content" in content
                assert "❌ Failed to fetch news from this source" in content
                assert "Test ChatGPT content" in content
        
        finally:
            # Clean up test file
            if os.path.exists(test_output_file):
                os.remove(test_output_file)
            if os.path.exists("test_outputs"):
                os.rmdir("test_outputs")
    
    @pytest.mark.asyncio
    async def test_fetch_and_save_news_integration(self):
        """Test the complete fetch and save workflow."""
        # Mock successful responses for all APIs
        mock_responses = {
            "perplexity": {"choices": [{"message": {"content": "Perplexity news"}}]},
            "claude": {"content": [{"text": "Claude news"}]},
            "chatgpt": {"choices": [{"message": {"content": "ChatGPT news"}}]}
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            
            def mock_json():
                call_count = mock_post.call_count
                if call_count == 1:
                    return mock_responses["perplexity"]
                elif call_count == 2:
                    return mock_responses["claude"]
                else:
                    return mock_responses["chatgpt"]
            
            mock_response.json = AsyncMock(side_effect=mock_json)
            mock_post.return_value.__aenter__.return_value = mock_response
            
            test_output_file = "test_outputs/integration_test.txt"
            
            try:
                summaries, saved_file = await self.fetcher.fetch_and_save_news(test_output_file)
                
                # Check summaries
                assert summaries["perplexity"] == "Perplexity news"
                assert summaries["claude"] == "Claude news"
                assert summaries["chatgpt"] == "ChatGPT news"
                
                # Check saved file
                assert saved_file == test_output_file
                assert os.path.exists(test_output_file)
                
            finally:
                # Clean up test file
                if os.path.exists(test_output_file):
                    os.remove(test_output_file)
                if os.path.exists("test_outputs"):
                    os.rmdir("test_outputs")

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
