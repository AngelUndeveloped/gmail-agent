from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.schema import AgentAction, AgentFinish
from typing import List, Dict, Any
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GmailAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-3.5-turbo",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
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
                subject = next(h['value'] for h in headers if h['name'] == 'Subject')
                sender = next(h['value'] for h in headers if h['name'] == 'From')
                
                emails.append({
                    'id': message['id'],
                    'subject': subject,
                    'sender': sender,
                    'snippet': msg['snippet']
                })

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
            subject = next(h['value'] for h in headers if h['name'] == 'Subject')
            sender = next(h['value'] for h in headers if h['name'] == 'From')
            body = message['snippet']

            # Process with LLM
            prompt = f"""
            Analyze this email:
            From: {sender}
            Subject: {subject}
            Content: {body}

            Provide a summary and suggested actions.
            """

            response = await self.llm.agenerate([prompt])
            
            return {
                'id': email_id,
                'subject': subject,
                'sender': sender,
                'summary': response.generations[0][0].text,
                'suggested_actions': response.generations[0][0].text
            }

        except HttpError as error:
            raise Exception(f'An error occurred: {error}') 