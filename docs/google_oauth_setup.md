# Google OAuth Setup Guide

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter a project name and click "Create"

## Step 2: Enable Gmail API

1. In the left sidebar, navigate to "APIs & Services" > "Library"
2. Search for "Gmail API"
3. Click on "Gmail API"
4. Click "Enable"

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type
3. Click "Create"

4. Fill in the application information:
   - App name: "Gmail Mail Merge"
   - User support email: Your email
   - Developer contact information: Your email

5. Click "Save and Continue"

6. Add scopes:
   - Click "Add or Remove Scopes"
   - Search for and select:
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/gmail.compose`
   - Click "Update"

7. Add test users:
   - Click "Add Users"
   - Enter the Gmail addresses you want to use
   - Click "Add"

8. Click "Save and Continue"

## Step 4: Create OAuth Client ID

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application"

4. Fill in the details:
   - Name: "Gmail Mail Merge Web Client"
   - Authorized JavaScript origins:
     - `http://localhost:5000`
   - Authorized redirect URIs:
     - `http://localhost:5000/oauth2callback`

5. Click "Create"

## Step 5: Download and Configure Client Secrets

1. In the OAuth 2.0 Client IDs list, find your client
2. Click the download button (⬇️) to download JSON
3. Rename the file to `client_secrets.json`

The file should look like this:
```json
{
  "web": {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-client-secret",
    "redirect_uris": ["http://localhost:5000/oauth2callback"]
  }
}
```

4. Place the file in your project's `client_secrets` directory

## Step 6: Configure Environment Variables

Update your `.env` file with the OAuth credentials:

```env
GOOGLE_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5000/oauth2callback
```

## Troubleshooting

### Common Issues

1. "Invalid Redirect URI"
   - Make sure the redirect URI exactly matches what's in your Google Cloud Console
   - Check for trailing slashes

2. "Access Not Configured"
   - Ensure Gmail API is enabled
   - Wait a few minutes after enabling the API

3. "Invalid Client"
   - Verify client ID and secret in .env file
   - Check if client_secrets.json is properly formatted

4. "Invalid Grant"
   - User needs to be added as a test user
   - Consent screen needs to be properly configured

### Verification Steps

1. Check API enabled:
   - Go to APIs & Services > Dashboard
   - Gmail API should show as enabled

2. Verify credentials:
   - Go to APIs & Services > Credentials
   - Check OAuth 2.0 Client IDs

3. Test user access:
   - Go to OAuth consent screen
   - Verify test users are listed

## Security Considerations

1. Keep client_secrets.json secure
2. Don't commit OAuth credentials to version control
3. Use environment variables for sensitive data
4. Regularly rotate client secrets
5. Monitor API usage in Google Cloud Console 