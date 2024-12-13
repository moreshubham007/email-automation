import unittest
import os
import tempfile
from app import create_app
from app.models import db, Project, GmailAccount, Template
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-key'

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create temp directory for client secrets
        self.temp_dir = tempfile.mkdtemp()
        self.app.config['CLIENT_SECRETS_DIR'] = self.temp_dir
        
        # Create mock client secret file
        self.client_secret_content = {
            "web": {
                "client_id": "test-client-id",
                "client_secret": "test-client-secret",
                "redirect_uris": ["http://localhost:5000/oauth2callback"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        # Clean up temp files
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.temp_dir) 