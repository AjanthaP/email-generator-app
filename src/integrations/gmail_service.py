"""
Gmail Integration Module for Email Generator App.

Provides Gmail API integration for sending emails, managing drafts,
and reading email context.
"""

import os
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pickle

try:
    from ..utils.config import settings as app_settings
except ImportError:
    # Fallback for when imported directly
    class MockSettings:
        enable_gmail = True
        disable_gmail = False
        gmail_credentials_file = "config/gmail_credentials.json"
        gmail_token_file = "data/gmail_token.pickle"
        gmail_scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/gmail.readonly'
        ]
    app_settings = MockSettings()

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("Gmail dependencies not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")


class GmailService:
    """
    Gmail API service for email operations.
    
    Features:
    - OAuth 2.0 authentication
    - Send emails with HTML/text content
    - Manage drafts
    - Read recent emails for context
    - Search emails by query
    - Get email thread context
    """
    
    def __init__(
        self,
        credentials_file: Optional[str] = None,
        token_file: Optional[str] = None,
        user_id: str = "me",
        scopes: Optional[List[str]] = None
    ):
        """
        Initialize Gmail service.
        
        Args:
            credentials_file: Path to OAuth 2.0 credentials file (uses config if None)
            token_file: Path to store authentication tokens (uses config if None)
            user_id: Gmail user ID (default: "me" for authenticated user)
            scopes: Gmail API scopes (uses config if None)
        """
        if not GMAIL_AVAILABLE:
            raise ImportError("Gmail dependencies not installed")
        
        # Use settings from config with parameter overrides
        self.credentials_file = credentials_file or app_settings.gmail_credentials_file
        self.token_file = token_file or app_settings.gmail_token_file
        self.user_id = user_id
        self.SCOPES = scopes or app_settings.gmail_scopes
        self.service = None
        self.credentials = None
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(credentials_file), exist_ok=True)
        os.makedirs(os.path.dirname(token_file), exist_ok=True)
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth 2.0.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Load existing token if available
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
            
            # Refresh or re-authenticate if needed
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    # Run OAuth flow
                    if not os.path.exists(self.credentials_file):
                        print(f"Gmail credentials file not found: {self.credentials_file}")
                        print("Please download OAuth 2.0 credentials from Google Cloud Console")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0)
                
                # Save credentials
                with open(self.token_file, 'wb') as token:
                    pickle.dump(self.credentials, token)
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            return True
            
        except Exception as e:
            print(f"Gmail authentication failed: {e}")
            return False
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: List[str] = None,
        bcc: List[str] = None,
        is_html: bool = True,
        reply_to_thread: str = None
    ) -> Optional[Dict]:
        """
        Send email via Gmail.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            is_html: Whether body is HTML (default: True)
            reply_to_thread: Thread ID to reply to (optional)
            
        Returns:
            Gmail API response dict or None if failed
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            # Create message
            message = MIMEMultipart('alternative') if is_html else MIMEText(body, 'plain')
            
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)
            
            if is_html:
                # Add both plain text and HTML versions
                text_part = MIMEText(self._html_to_text(body), 'plain')
                html_part = MIMEText(body, 'html')
                message.attach(text_part)
                message.attach(html_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Prepare request body
            send_request = {'raw': raw_message}
            if reply_to_thread:
                send_request['threadId'] = reply_to_thread
            
            # Send email
            result = self.service.users().messages().send(
                userId=self.user_id,
                body=send_request
            ).execute()
            
            return {
                'message_id': result.get('id'),
                'thread_id': result.get('threadId'),
                'status': 'sent',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except HttpError as e:
            print(f"Gmail API error: {e}")
            return None
        except Exception as e:
            print(f"Error sending email: {e}")
            return None
    
    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: List[str] = None,
        bcc: List[str] = None,
        is_html: bool = True
    ) -> Optional[Dict]:
        """
        Create Gmail draft.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            is_html: Whether body is HTML (default: True)
            
        Returns:
            Gmail draft response dict or None if failed
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            # Create message (same as send_email but for draft)
            message = MIMEMultipart('alternative') if is_html else MIMEText(body, 'plain')
            
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = ', '.join(cc)
            if bcc:
                message['bcc'] = ', '.join(bcc)
            
            if is_html:
                text_part = MIMEText(self._html_to_text(body), 'plain')
                html_part = MIMEText(body, 'html')
                message.attach(text_part)
                message.attach(html_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Create draft
            draft_request = {
                'message': {
                    'raw': raw_message
                }
            }
            
            result = self.service.users().drafts().create(
                userId=self.user_id,
                body=draft_request
            ).execute()
            
            return {
                'draft_id': result.get('id'),
                'message_id': result.get('message', {}).get('id'),
                'status': 'draft_created',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except HttpError as e:
            print(f"Gmail API error creating draft: {e}")
            return None
        except Exception as e:
            print(f"Error creating draft: {e}")
            return None
    
    def get_recent_emails(
        self,
        limit: int = 10,
        query: str = None,
        days_back: int = 7
    ) -> List[Dict]:
        """
        Get recent emails for context.
        
        Args:
            limit: Maximum number of emails to retrieve
            query: Gmail search query (optional)
            days_back: Number of days to look back
            
        Returns:
            List of email dicts with content and metadata
        """
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            # Build search query
            search_query = ""
            if query:
                search_query += f"{query} "
            
            # Add date filter
            after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            search_query += f"after:{after_date}"
            
            # Search for messages
            results = self.service.users().messages().list(
                userId=self.user_id,
                q=search_query,
                maxResults=limit
            ).execute()
            
            messages = results.get('messages', [])
            
            email_list = []
            for message in messages:
                try:
                    # Get full message details
                    msg = self.service.users().messages().get(
                        userId=self.user_id,
                        id=message['id'],
                        format='full'
                    ).execute()
                    
                    # Extract email data
                    email_data = self._extract_email_data(msg)
                    if email_data:
                        email_list.append(email_data)
                        
                except Exception as e:
                    print(f"Error processing email {message['id']}: {e}")
                    continue
            
            return email_list
            
        except HttpError as e:
            print(f"Gmail API error: {e}")
            return []
        except Exception as e:
            print(f"Error retrieving emails: {e}")
            return []
    
    def get_thread_context(self, thread_id: str) -> Optional[Dict]:
        """
        Get email thread context for replies.
        
        Args:
            thread_id: Gmail thread ID
            
        Returns:
            Thread context dict or None if failed
        """
        if not self.service:
            if not self.authenticate():
                return None
        
        try:
            # Get thread
            thread = self.service.users().threads().get(
                userId=self.user_id,
                id=thread_id,
                format='full'
            ).execute()
            
            messages = thread.get('messages', [])
            if not messages:
                return None
            
            # Extract thread context
            context = {
                'thread_id': thread_id,
                'message_count': len(messages),
                'messages': [],
                'participants': set(),
                'subject': None
            }
            
            for message in messages:
                email_data = self._extract_email_data(message)
                if email_data:
                    context['messages'].append(email_data)
                    context['participants'].add(email_data.get('from', ''))
                    if not context['subject']:
                        context['subject'] = email_data.get('subject', '')
            
            context['participants'] = list(context['participants'])
            return context
            
        except HttpError as e:
            print(f"Gmail API error: {e}")
            return None
        except Exception as e:
            print(f"Error getting thread context: {e}")
            return None
    
    def _extract_email_data(self, message: Dict) -> Optional[Dict]:
        """Extract email data from Gmail message."""
        try:
            headers = message.get('payload', {}).get('headers', [])
            
            # Extract headers
            email_data = {
                'message_id': message.get('id'),
                'thread_id': message.get('threadId'),
                'timestamp': None,
                'from': None,
                'to': None,
                'subject': None,
                'body': None,
                'is_html': False
            }
            
            # Parse headers
            for header in headers:
                name = header.get('name', '').lower()
                value = header.get('value', '')
                
                if name == 'from':
                    email_data['from'] = value
                elif name == 'to':
                    email_data['to'] = value
                elif name == 'subject':
                    email_data['subject'] = value
                elif name == 'date':
                    try:
                        # Convert date to ISO format
                        from email.utils import parsedate_to_datetime
                        dt = parsedate_to_datetime(value)
                        email_data['timestamp'] = dt.isoformat()
                    except:
                        email_data['timestamp'] = value
            
            # Extract body
            body_text = self._extract_body(message.get('payload', {}))
            if body_text:
                email_data['body'] = body_text[0]
                email_data['is_html'] = body_text[1]
            
            return email_data
            
        except Exception as e:
            print(f"Error extracting email data: {e}")
            return None
    
    def _extract_body(self, payload: Dict) -> Optional[tuple]:
        """Extract body text from email payload."""
        try:
            # Handle multipart messages
            if payload.get('parts'):
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/html':
                        body_data = part.get('body', {}).get('data')
                        if body_data:
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            return (body, True)
                    elif part.get('mimeType') == 'text/plain':
                        body_data = part.get('body', {}).get('data')
                        if body_data:
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                            return (body, False)
                
                # Recursively check nested parts
                for part in payload['parts']:
                    if part.get('parts'):
                        result = self._extract_body(part)
                        if result:
                            return result
            
            # Handle single part messages
            elif payload.get('body', {}).get('data'):
                body_data = payload['body']['data']
                body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                mime_type = payload.get('mimeType', 'text/plain')
                is_html = mime_type == 'text/html'
                return (body, is_html)
            
            return None
            
        except Exception as e:
            print(f"Error extracting body: {e}")
            return None
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML to plain text (simple version)."""
        try:
            import re
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', html_content)
            # Decode HTML entities
            import html
            text = html.unescape(text)
            return text.strip()
        except:
            return html_content
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get Gmail service status."""
        return {
            "authenticated": self.service is not None,
            "credentials_file_exists": os.path.exists(self.credentials_file),
            "token_file_exists": os.path.exists(self.token_file),
            "gmail_available": GMAIL_AVAILABLE,
            "scopes": self.SCOPES,
            "user_id": self.user_id
        }


# Factory function
def create_gmail_service(
    use_gmail: Optional[bool] = None,
    credentials_file: Optional[str] = None,
    **kwargs
) -> Optional[GmailService]:
    """
    Factory function to create Gmail service.
    
    Args:
        use_gmail: Whether to use Gmail integration (uses config if None)
        credentials_file: Path to Gmail credentials (uses config if None)
        **kwargs: Additional Gmail service parameters
        
    Returns:
        GmailService instance or None if disabled
    """
    # Use settings to determine if Gmail should be enabled
    use_gmail = use_gmail if use_gmail is not None else app_settings.enable_gmail
    
    # Check if Gmail is disabled via settings
    if not use_gmail or app_settings.disable_gmail:
        return None
    
    if not GMAIL_AVAILABLE:
        print("Gmail integration disabled: dependencies not installed")
        return None
    
    try:
        return GmailService(credentials_file=credentials_file, **kwargs)
    except Exception as e:
        print(f"Failed to initialize Gmail service: {e}")
        return None