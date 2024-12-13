from unittest.mock import patch, MagicMock
import json
import os
from .test_base import BaseTestCase
from app.models import Project, GmailAccount

class TestOAuth(BaseTestCase):
    def setUp(self):
        super().setUp()
        # Create test project and Gmail account
        self.project = Project(
            name='Test Project',
            description='Test Description',
            client_secret_path=os.path.join(self.temp_dir, 'client_secret.json')
        )
        db.session.add(self.project)
        
        self.gmail_account = GmailAccount(
            email='test@gmail.com',
            description='Test Account',
            project=self.project
        )
        db.session.add(self.gmail_account)
        db.session.commit()
        
        # Save mock client secret file
        with open(self.project.client_secret_path, 'w') as f:
            json.dump(self.client_secret_content, f)

    @patch('app.utils.oauth_utils.Flow')
    def test_authentication_start(self, mock_flow):
        # Mock the Flow class
        mock_flow_instance = MagicMock()
        mock_flow_instance.authorization_url.return_value = ('http://auth-url', 'state-token')
        mock_flow.from_client_secrets_file.return_value = mock_flow_instance
        
        response = self.client.get(f'/authenticate/{self.gmail_account.email}')
        
        # Check redirect to auth URL
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.startswith('http://auth-url'))
        
        # Verify Flow was called correctly
        mock_flow.from_client_secrets_file.assert_called_once()
        mock_flow_instance.authorization_url.assert_called_once()

    @patch('app.utils.oauth_utils.Flow')
    @patch('app.utils.oauth_utils.build')
    def test_oauth_callback(self, mock_build, mock_flow):
        # Mock the Flow class
        mock_flow_instance = MagicMock()
        mock_credentials = MagicMock()
        mock_credentials.token = 'test-token'
        mock_credentials.refresh_token = 'test-refresh-token'
        mock_flow_instance.credentials = mock_credentials
        mock_flow.from_client_secrets_file.return_value = mock_flow_instance
        
        # Mock Gmail API service
        mock_service = MagicMock()
        mock_profile = {'emailAddress': self.gmail_account.email}
        mock_service.users().getProfile().execute.return_value = mock_profile
        mock_build.return_value = mock_service
        
        # Set session variables
        with self.client.session_transaction() as session:
            session['oauth_state'] = 'test-state'
            session['authenticating_email'] = self.gmail_account.email
        
        # Make callback request
        response = self.client.get('/oauth2callback?state=test-state&code=test-code')
        
        # Check redirect and authentication status
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/gmail-management')
        
        # Verify account was authenticated
        self.gmail_account = GmailAccount.query.get(self.gmail_account.id)
        self.assertTrue(self.gmail_account.authenticated)
        self.assertIsNotNone(self.gmail_account.credentials)

    def test_revoke_access(self):
        # Set up authenticated account
        self.gmail_account.authenticated = True
        self.gmail_account.credentials = json.dumps({
            'token': 'test-token',
            'refresh_token': 'test-refresh-token',
            'token_uri': 'test-uri',
            'client_id': 'test-id',
            'client_secret': 'test-secret',
            'scopes': ['test-scope']
        })
        db.session.commit()
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            
            response = self.client.post(f'/api/gmail/{self.gmail_account.email}/revoke')
            
            self.assertEqual(response.status_code, 200)
            
            # Verify account was de-authenticated
            self.gmail_account = GmailAccount.query.get(self.gmail_account.id)
            self.assertFalse(self.gmail_account.authenticated)
            self.assertIsNone(self.gmail_account.credentials) 