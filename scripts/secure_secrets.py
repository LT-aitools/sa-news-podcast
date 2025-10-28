# ABOUTME: Secure secrets management for South African news podcast
# ABOUTME: Loads API keys and credentials from ~/.config/sa-podcast/secrets.json

import json
import os
from pathlib import Path

def get_secrets_file_path():
    """Get the path to the secrets file in ~/.config/sa-podcast/"""
    config_dir = Path.home() / ".config" / "sa-podcast"
    return config_dir / "secrets.json"

def load_secrets():
    """Load secrets from environment variables (GitHub Actions) or ~/.config/sa-podcast/secrets.json (local)"""
    
    # First, try to load from environment variables (GitHub Actions mode)
    if os.getenv('OPENAI_API_KEY'):
        print("Using environment variables for secrets (GitHub Actions mode)")
        print(f"OPENAI_API_KEY present: {bool(os.getenv('OPENAI_API_KEY'))}")
        print(f"AZURE_SPEECH_KEY present: {bool(os.getenv('AZURE_SPEECH_KEY'))}")
        print(f"AZURE_SPEECH_REGION present: {bool(os.getenv('AZURE_SPEECH_REGION'))}")
        return {
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'claude_api_key': os.getenv('CLAUDE_API_KEY'),
            'azure_speech_key': os.getenv('AZURE_SPEECH_KEY'),
            'azure_speech_region': os.getenv('AZURE_SPEECH_REGION'),
            'email': {
                'address': os.getenv('EMAIL_ADDRESS'),
                'password': os.getenv('EMAIL_PASSWORD'),
                'imap_server': os.getenv('IMAP_SERVER', 'imap.gmail.com')
            },
            'cleanup': {
                'secret_key': os.getenv('CLEANUP_SECRET_KEY')
            }
        }
    
    # Fallback to local secrets.json file
    secrets_file = get_secrets_file_path()
    
    if not secrets_file.exists():
        raise FileNotFoundError(
            f"Secrets file not found at {secrets_file}\n"
            f"Please create the file with your API keys and credentials.\n"
            f"Or set environment variables for GitHub Actions mode."
        )
    
    try:
        with open(secrets_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in secrets file: {e}")
    except Exception as e:
        raise Exception(f"Error reading secrets file: {e}")

def get_openai_api_key():
    """Get OpenAI API key from secrets file"""
    secrets = load_secrets()
    return secrets.get('openai_api_key')

def get_claude_api_key():
    """Get Claude API key from secrets file"""
    secrets = load_secrets()
    return secrets.get('claude_api_key')

def get_azure_speech_key():
    """Get Azure Speech Service key from secrets file"""
    secrets = load_secrets()
    return secrets.get('azure_speech_key')

def get_azure_speech_region():
    """Get Azure Speech Service region from secrets file"""
    secrets = load_secrets()
    return secrets.get('azure_speech_region')

def get_email_credentials():
    """Get email credentials from secrets file"""
    secrets = load_secrets()
    email_section = secrets.get('email', {})
    return {
        'address': email_section.get('address'),
        'password': email_section.get('password'),
        'imap_server': email_section.get('imap_server', 'imap.gmail.com')
    }

def get_cleanup_secret_key():
    """Get cleanup secret key from secrets file"""
    secrets = load_secrets()
    cleanup_section = secrets.get('cleanup', {})
    return cleanup_section.get('secret_key')
