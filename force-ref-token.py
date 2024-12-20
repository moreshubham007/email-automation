from app import create_app, db
from app.models import GmailAccount
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def force_refresh_tokens():
    app = create_app()
    with app.app_context():
        accounts = GmailAccount.query.filter_by(authenticated=True).all()
        
        for account in account:
            try:
                print(f"Processing account: {account.email}")
                
                # Load existing credentials
                creds_data = json.loads(account.credentials)
                credentials = Credentials(
                    token=creds_data['token'],
                    refresh_token=creds_data['refresh_token'],
                    token_uri=creds_data['token_uri'],
                    client_id=creds_data['client_id'],
                    client_secret=creds_data['client_secret'],
                    scopes=[
                        'https://www.googleapis.com/auth/gmail.send',
                        'https://www.googleapis.com/auth/gmail.compose',
                        'https://www.googleapis.com/auth/userinfo.profile',
                        'https://www.googleapis.com/auth/userinfo.email',
                        'https://www.googleapis.com/auth/contacts.readonly'
                    ]
                )

                # Force token refresh
                if credentials.expired:
                    credentials.refresh(Request())
                    
                    # Update stored credentials
                    account.credentials = json.dumps({
                        'token': credentials.token,
                        'refresh_token': credentials.refresh_token,
                        'token_uri': credentials.token_uri,
                        'client_id': credentials.client_id,
                        'client_secret': credentials.client_secret,
                        'scopes': credentials.scopes
                    })
                    account.authenticated = True
                    db.session.commit()
                    print(f"Successfully refreshed token for {account.email}")
                
            except Exception as e:
                print(f"Error processing {account.email}: {str(e)}")
                account.authenticated = False
                db.session.commit()

if __name__ == '__main__':
    force_refresh_tokens() 