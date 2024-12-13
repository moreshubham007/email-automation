import os
from pathlib import Path
from datetime import timedelta

basedir = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change'
    
    # Create instance directory if it doesn't exist
    INSTANCE_PATH = basedir / 'instance'
    INSTANCE_PATH.mkdir(exist_ok=True, parents=True)
    
    # Database configuration - use absolute path
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{Path.home() / "gmail_merge.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Directory for storing client secrets
    CLIENT_SECRETS_DIR = basedir / 'client_secrets'
    CLIENT_SECRETS_DIR.mkdir(exist_ok=True)
    
    # OAuth Settings
    GOOGLE_OAUTH_SCOPES = [
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.compose'
    ]
    
    # For development
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Remove in production
    
    # Add other configuration settings here 
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)