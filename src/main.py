from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from dotenv import load_dotenv
import os

from .gmail_agent import GmailAgent
from .auth import get_auth_url, handle_callback

# Load environment variables
load_dotenv()

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
    return await handle_callback(code)

@app.post("/emails/search")
async def search_emails(request: EmailRequest):
    """Search emails using the Gmail Agent"""
    try:
        results = await gmail_agent.search_emails(request.query, request.max_results)
        return {"emails": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 