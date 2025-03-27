from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from dotenv import load_dotenv
import os
from google.oauth2.credentials import Credentials

from .gmail_agent import GmailAgent
from .auth import get_auth_url, handle_callback
from .utils.secrets import secrets

# Load environment variables
load_dotenv()

# Validate secrets on startup
try:
    secrets.validate_secrets()
except ValueError as e:
    print(f"Error: {e}")
    print("Please ensure all required secrets are set in your .env file")
    exit(1)

app = FastAPI(title="Gmail Agent API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gmail Agent
gmail_agent = GmailAgent()

class EmailRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10

class EmailAnalysisRequest(BaseModel):
    email_id: str

@app.get("/")
async def root():
    return {"message": "Gmail Agent API is running"}

@app.get("/auth")
async def auth():
    """Get the Google OAuth URL"""
    return {"url": get_auth_url()}

@app.get("/auth/callback")
async def auth_callback(code: str):
    """Handle the OAuth callback"""
    creds_dict = await handle_callback(code)
    
    # Create Credentials object from the dictionary
    credentials = Credentials(
        token=creds_dict["token"],
        refresh_token=creds_dict["refresh_token"],
        token_uri=creds_dict["token_uri"],
        client_id=creds_dict["client_id"],
        client_secret=creds_dict["client_secret"],
        scopes=creds_dict["scopes"]
    )
    
    # Set credentials in the Gmail agent
    gmail_agent.set_credentials(credentials)
    
    return {"message": "Authentication successful"}

@app.post("/emails/search")
async def search_emails(request: EmailRequest):
    """Search emails using the Gmail Agent"""
    try:
        results = await gmail_agent.search_emails(request.query, request.max_results)
        return {"emails": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/emails/analyze/{email_id}")
async def analyze_email(email_id: str):
    """Analyze an email using the Gmail Agent"""
    try:
        # Get the specific email directly instead of searching
        email = await gmail_agent.get_email(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Analyze the email
        analysis = await gmail_agent.analyze_email(email)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 