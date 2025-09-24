# ABOUTME: Pytest configuration and shared fixtures for SA News Podcast tests
# ABOUTME: Provides common test setup and configuration

import pytest
import os
import tempfile
import sys
from unittest.mock import Mock

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_secrets():
    """Mock secrets object for testing."""
    secrets = Mock()
    secrets.get_perplexity_api_key.return_value = "test_perplexity_key"
    secrets.get_claude_api_key.return_value = "test_claude_key"
    secrets.get_openai_api_key.return_value = "test_openai_key"
    secrets.get_azure_speech_key.return_value = "test_azure_key"
    secrets.get_azure_speech_region.return_value = "test_region"
    secrets.get_cleanup_secret_key.return_value = "test_cleanup_key"
    return secrets

@pytest.fixture
def temp_transcript_file():
    """Create a temporary transcript file for testing."""
    test_transcript = """**intro music**

Howzit South Africa, and welcome to Mzansi Lowdown, your daily dose of news coming out of the Republic. I am your A.I. host, Leah.

Today is Monday, January 15, 2024.

In today's news, there are several important developments across South Africa.

**transition music**

In other news, the government has announced new policies.

**outro music**"""
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(test_transcript)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.remove(temp_file)

@pytest.fixture
def temp_news_digests_file():
    """Create a temporary news digests file for testing."""
    test_digests = """AI NEWS DIGESTS FOR SOUTH AFRICAN PODCAST
==================================================
Generated on: 2024-01-15 10:00:00
Web search prompt: What are today's most important South African news stories?

==================== PERPLEXITY NEWS DIGEST ====================
Test Perplexity news content about South Africa

==================== CLAUDE NEWS DIGEST ====================
Test Claude news content about South Africa

==================== CHATGPT NEWS DIGEST ====================
Test ChatGPT news content about South Africa"""
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(test_digests)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.remove(temp_file)

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    # Cleanup
    import shutil
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Ensure we're in a clean state
    original_cwd = os.getcwd()
    
    yield
    
    # Restore original state
    os.chdir(original_cwd)

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add e2e marker to end-to-end tests
        if "end_to_end" in item.nodeid or "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
        
        # Add slow marker to tests that might take longer
        if any(keyword in item.nodeid for keyword in ["workflow", "complete", "full"]):
            item.add_marker(pytest.mark.slow)
