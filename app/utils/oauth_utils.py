import json
import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
import requests
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import base64

SCOPES = [
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify'
]

class OAuth2Error(Exception):
    """Custom exception for OAuth2 errors"""
    pass

class OAuth2Handler:
    def __init__(self, client_secrets_file):
        if not os.path.exists(client_secrets_file):
            raise OAuth2Error(f"Client secrets file not found: {client_secrets_file}")
        self.client_secrets_file = client_secrets_file
        
    def get_authorization_url(self, email, state):
        """Create OAuth2 flow and get authorization URL"""
        try:
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=SCOPES,
                redirect_uri="http://localhost:5000/oauth2callback"
            )
            
            flow.state = state
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                login_hint=email,
                include_granted_scopes='true',
                prompt='consent'
            )
            
            return authorization_url, state
        except Exception as e:
            raise OAuth2Error(f"Failed to create authorization URL: {str(e)}")
        
    def handle_oauth2_callback(self, state, code):
        """Handle OAuth2 callback and return credentials"""
        try:
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=SCOPES,
                state=state,
                redirect_uri="http://localhost:5000/oauth2callback"
            )
            
            flow.fetch_token(code=code)
            return flow.credentials
        except Exception as e:
            raise OAuth2Error(f"Failed to handle OAuth callback: {str(e)}")

    @staticmethod
    def verify_gmail_access(credentials):
        """Verify Gmail API access with credentials"""
        try:
            service = build('gmail', 'v1', credentials=credentials)
            profile = service.users().getProfile(userId='me').execute()
            return True, profile['emailAddress']
        except RefreshError:
            raise OAuth2Error("Token refresh failed. Re-authentication required.")
        except Exception as e:
            raise OAuth2Error(f"Failed to verify Gmail access: {str(e)}")

    @staticmethod
    def revoke_access(credentials):
        """Revoke OAuth2 access"""
        try:
            if isinstance(credentials, dict):
                credentials = Credentials(**credentials)
            
            # Revoke token
            requests.post('https://oauth2.googleapis.com/revoke',
                        params={'token': credentials.token},
                        headers={'content-type': 'application/x-www-form-urlencoded'})
            
            return True
        except Exception as e:
            raise OAuth2Error(f"Failed to revoke access: {str(e)}")

    @staticmethod
    def credentials_to_dict(credentials):
        """Convert credentials to dictionary for storage"""
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

    @staticmethod
    def dict_to_credentials(credentials_dict):
        """Convert dictionary back to credentials object"""
        return Credentials(
            token=credentials_dict['token'],
            refresh_token=credentials_dict['refresh_token'],
            token_uri=credentials_dict['token_uri'],
            client_id=credentials_dict['client_id'],
            client_secret=credentials_dict['client_secret'],
            scopes=credentials_dict['scopes']
        )

    def create_draft(self, credentials, to_email, subject, body_html):
        """Create a draft email using Gmail API"""
        try:
            service = build('gmail', 'v1', credentials=credentials)
            
            # Create message
            message = MIMEText(body_html, 'html')
            message['to'] = to_email
            message['subject'] = subject
            
            # Encode the message
            raw = base64.urlsafe_b64encode(message.as_bytes())
            raw = raw.decode()
            
            # Create the draft
            draft = service.users().drafts().create(
                userId='me',
                body={
                    'message': {
                        'raw': raw
                    }
                }
            ).execute()
            
            return True, draft['id']
            
        except HttpError as error:
            if error.resp.status == 401:
                raise OAuth2Error("Authentication expired. Please re-authenticate.")
            elif error.resp.status == 403:
                raise OAuth2Error("Permission denied. Check Gmail API scopes.")
            else:
                raise OAuth2Error(f"Gmail API error: {str(error)}")
        except Exception as e:
            raise OAuth2Error(f"Failed to create draft: {str(e)}")