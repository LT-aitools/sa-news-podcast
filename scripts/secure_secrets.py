# ABOUTME: Secure secrets loader for SA Podcast project
# ABOUTME: Loads API keys and secrets from file-based storage outside project folder

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class SecureSecrets:
    """
    Secure secrets manager that loads API keys from file-based storage
    outside the project folder as per security requirements.
    """
    
    def __init__(self, secrets_file_path: Optional[str] = None):
        """
        Initialize the secrets manager.
        
        Args:
            secrets_file_path: Path to secrets file. Defaults to ~/.config/sa-podcast/secrets.json
        """
        if secrets_file_path is None:
            # Default to secure location outside project folder
            home_dir = Path.home()
            self.secrets_file = home_dir / ".config" / "sa-podcast" / "secrets.json"
        else:
            self.secrets_file = Path(secrets_file_path)
        
        self._secrets: Dict[str, Any] = {}
        self._load_secrets()
    
    def _load_secrets(self) -> None:
        """Load secrets from the configured file."""
        try:
            if not self.secrets_file.exists():
                raise FileNotFoundError(
                    f"Secrets file not found at {self.secrets_file}. "
                    f"Please create it using the template at {self.secrets_file.parent}/secrets.json.template"
                )
            
            with open(self.secrets_file, 'r') as f:
                self._secrets = json.load(f)
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in secrets file: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to load secrets: {e}")
    
    def get_azure_speech_key(self) -> str:
        """Get Azure Speech API subscription key."""
        try:
            return self._secrets["azure_speech"]["subscription_key"]
        except KeyError:
            raise KeyError("Azure Speech subscription key not found in secrets file")
    
    def get_azure_speech_region(self) -> str:
        """Get Azure Speech API region."""
        try:
            return self._secrets["azure_speech"]["region"]
        except KeyError:
            raise KeyError("Azure Speech region not found in secrets file")
    
    
    def get_claude_api_key(self) -> str:
        """Get Claude API key."""
        try:
            return self._secrets["claude"]["api_key"]
        except KeyError:
            raise KeyError("Claude API key not found in secrets file")
    
    def get_openai_api_key(self) -> str:
        """Get OpenAI API key."""
        try:
            return self._secrets["openai"]["api_key"]
        except KeyError:
            raise KeyError("OpenAI API key not found in secrets file")
    
    def get_perplexity_api_key(self) -> str:
        """Get Perplexity API key."""
        try:
            return self._secrets["perplexity"]["api_key"]
        except KeyError:
            raise KeyError("Perplexity API key not found in secrets file")
    
    
    def get_cleanup_secret_key(self) -> str:
        """Get cleanup secret key."""
        try:
            return self._secrets["cleanup"]["secret_key"]
        except KeyError:
            raise KeyError("Cleanup secret key not found in secrets file")
    
    def get_secret(self, path: str) -> Any:
        """
        Get a secret value using dot notation (e.g., 'azure_speech.subscription_key').
        
        Args:
            path: Dot-separated path to the secret
            
        Returns:
            The secret value
            
        Raises:
            KeyError: If the path doesn't exist
        """
        keys = path.split('.')
        value = self._secrets
        
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                raise KeyError(f"Secret path '{path}' not found")
            value = value[key]
        
        return value

# Global instance for easy access
_secrets_instance: Optional[SecureSecrets] = None

def get_secrets() -> SecureSecrets:
    """Get the global secrets instance."""
    global _secrets_instance
    if _secrets_instance is None:
        _secrets_instance = SecureSecrets()
    return _secrets_instance
