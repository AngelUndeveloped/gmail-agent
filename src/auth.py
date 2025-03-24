from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
from .utils.secrets import secrets

load_dotenv()

# OAuth 2.0 configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_auth_url() -> str:
    """Generate the Google OAuth URL"""
    client_config = {
        "web": {
            "client_id": secrets.get_secret('GOOGLE_CLIENT_ID'),
            "client_secret": secrets.get_secret('GOOGLE_CLIENT_SECRET'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [secrets.get_secret('GOOGLE_REDIRECT_URI')],
        }
    }
    
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES
    )
    flow.redirect_uri = secrets.get_secret('GOOGLE_REDIRECT_URI')
    
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    return auth_url

async def handle_callback(code: str) -> dict:
    """Handle the OAuth callback and return credentials"""
    client_config = {
        "web": {
            "client_id": secrets.get_secret('GOOGLE_CLIENT_ID'),
            "client_secret": secrets.get_secret('GOOGLE_CLIENT_SECRET'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [secrets.get_secret('GOOGLE_REDIRECT_URI')],
        }
    }
    
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES
    )
    flow.redirect_uri = secrets.get_secret('GOOGLE_REDIRECT_URI')
    
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    } 