from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import Tool
from langchain_core.memory import BaseMemory
from langchain_core.chat_history import BaseChatMessageHistory
from typing import List, Dict, Any, Optional
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .utils.secrets import secrets
from pydantic import Field
import google.generativeai as genai

# Configure the Gemini API
genai.configure(api_key=secrets.get_secret('GEMINI_API_KEY'))

class SimpleMemory(BaseMemory):
    chat_history: List[Dict[str, str]] = Field(default_factory=list)
    memory_key: str = Field(default="chat_history")
    memory_variables: List[str] = Field(default_factory=lambda: ["chat_history"])

    @property
    def memory_variables(self) -> List[str]:
        return self.memory_variables

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {self.memory_key: self.chat_history}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        self.chat_history.append({
            "input": inputs.get("input", ""),
            "output": outputs.get("output", "")
        })

    def clear(self) -> None:
        self.chat_history = []

class GmailAgent:
    def __init__(self):
        self.client = genai.GenerativeModel(
            model_name="gemini-2.0-flash-thinking-exp-01-21",
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=64,
                max_output_tokens=65536,
            )
        )
        self.memory = SimpleMemory()
        self.credentials = None
        self.service = None

    def set_credentials(self, credentials: Credentials):
        """Set Gmail API credentials"""
        self.credentials = credentials
        self.service = build('gmail', 'v1', credentials=credentials)

    async def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search emails using Gmail API"""
        if not self.service:
            raise Exception("Gmail service not initialized. Please authenticate first.")

        try:
            # Search for emails
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            emails = []

            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                
                emails.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'snippet': msg['snippet']
                })

            # Store in memory for context
            self.memory.save_context(
                {"input": f"Searched for: {query}"},
                {"output": f"Found {len(emails)} emails"}
            )

            return emails

        except HttpError as error:
            raise Exception(f'An error occurred: {error}')

    async def process_email(self, email_id: str) -> Dict[str, Any]:
        """Process a single email using the agent"""
        if not self.service:
            raise Exception("Gmail service not initialized. Please authenticate first.")

        try:
            # Get email details
            message = self.service.users().messages().get(
                userId='me',
                id=email_id
            ).execute()

            # Extract email content
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            body = message['snippet']

            # Process with LLM
            context = self.memory.load_memory_variables({})
            prompt = f"""
            Based on previous interactions and this email:
            From: {sender}
            Subject: {subject}
            Content: {body}

            Previous Context: {context.get('chat_history', 'No previous context')}

            Provide a summary and suggested actions.
            """

            response = await self.llm.agenerate([prompt])
            
            # Store in memory
            self.memory.save_context(
                {"input": f"Processed email: {subject}"},
                {"output": response.generations[0][0].text}
            )
            
            return {
                'id': email_id,
                'subject': subject,
                'sender': sender,
                'summary': response.generations[0][0].text,
                'suggested_actions': response.generations[0][0].text
            }

        except HttpError as error:
            raise Exception(f'An error occurred: {error}')

    async def analyze_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an email using Gemini AI"""
        if not self.service:
            raise Exception("Gmail service not initialized. Please authenticate first.")

        prompt = f"""
        Please analyze this email and provide:
        1. A brief summary
        2. Key action items (if any)
        3. Priority level (High/Medium/Low)
        4. Suggested response points (if a response is needed)

        Email Details:
        From: {email_data['sender']}
        Subject: {email_data['subject']}
        Content: {email_data['snippet']}
        """

        # Get analysis from Gemini
        response = self.client.generate_content(prompt)
        response_text = response.text

        # Store in memory for context
        self.memory.save_context(
            {"input": f"Analyzed email: {email_data['subject']}"},
            {"output": response_text}
        )

        return {
            'email_id': email_data['id'],
            'analysis': response_text
        }

    async def get_email(self, email_id: str) -> Dict[str, Any]:
        """Get a specific email by ID"""
        if not self.service:
            raise Exception("Gmail service not initialized. Please authenticate first.")

        try:
            # Get the specific email
            msg = self.service.users().messages().get(
                userId='me',
                id=email_id
            ).execute()
            
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            
            return {
                'id': email_id,
                'subject': subject,
                'sender': sender,
                'snippet': msg['snippet']
            }

        except HttpError as error:
            raise Exception(f'An error occurred: {error}') 