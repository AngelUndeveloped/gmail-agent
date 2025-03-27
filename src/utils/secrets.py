import os
from typing import Optional
from dotenv import load_dotenv

class SecretsManager:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # Define required secrets
        self.required_secrets = {
            'GOOGLE_CLIENT_ID': 'Google OAuth Client ID',
            'GOOGLE_CLIENT_SECRET': 'Google OAuth Client Secret',
            'GOOGLE_REDIRECT_URI': 'Google OAuth Redirect URI',
            'GEMINI_API_KEY': 'Gemini API Key'
        }

    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret value from environment variables"""
        value = os.getenv(key)
        if not value and key in self.required_secrets:
            raise ValueError(f"Missing required secret: {self.required_secrets[key]}")
        return value

    def validate_secrets(self) -> bool:
        """Validate that all required secrets are present"""
        missing_secrets = []
        for key, description in self.required_secrets.items():
            if not os.getenv(key):
                missing_secrets.append(description)
        
        if missing_secrets:
            raise ValueError(f"Missing required secrets: {', '.join(missing_secrets)}")
        return True

    @staticmethod
    def get_environment() -> str:
        """Get the current environment (development/production)"""
        return os.getenv('ENVIRONMENT', 'development')

# Create a global instance
secrets = SecretsManager() 