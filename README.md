# Gmail Mail Merge Application

A Flask-based web application for managing Gmail accounts and sending personalized mass emails using Gmail API.

## Features

- Multiple Gmail account management
- Project-based organization
- Email template management with placeholders
- CSV-based mail merge
- OAuth2 authentication with Gmail
- Rate limiting and quota management

## Prerequisites

- Python 3.7 or higher
- A Google Cloud Platform account
- Gmail accounts for sending emails

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/flask-gmail-app.git
cd flask-gmail-app
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

5. Initialize the database:
```bash
flask db upgrade
```

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

4. Configure OAuth consent screen:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Select "External" user type
   - Fill in the application name and developer contact information
   - Add the following scopes:
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/gmail.compose`
   - Add your test users (Gmail addresses)

5. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:5000/oauth2callback` (for development)
     - Your production URL (if applicable)
   - Download the client secrets JSON file
   - Rename it to `client_secrets.json`
   - Place it in the `client_secrets` directory

## Project Structure

```
flask_gmail_app/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── forms.py
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
├── instance/
├── client_secrets/
├── migrations/
├── .env
├── config.py
└── requirements.txt
```

## Usage

1. Start the development server:
```bash
flask run
```

2. Access the application at `http://localhost:5000`

3. Create a new project:
   - Click "Gmail Management"
   - Add a new project with your client secrets file

4. Add Gmail accounts:
   - Individual accounts: Use "Add Individual ID"
   - Bulk import: Use "Upload CSV"

5. Create email templates:
   - Go to "Template Management"
   - Create templates with placeholders like {{name}}, {{email}}

6. Send mail merge:
   - Go to "Mail Merge"
   - Select template and upload recipient CSV
   - Preview and send emails

## Placeholder System

Templates support dynamic content using placeholders:
- Basic: `{{name}}`, `{{email}}`, `{{company}}`
- Can be used in both subject and body
- CSV headers should match placeholder names

Example template:
```
Subject: Welcome to {{company}}, {{name}}!

Dear {{name}},

Thank you for joining {{company}}. Your registered email is {{email}}.

Best regards,
The Team
```

## Rate Limiting

The application respects Gmail's sending limits:
- 2,000 emails per day per account
- Maximum 250 recipients per email
- 500 emails per day for trial users

## Error Handling

- Invalid email formats
- Authentication failures
- Rate limit exceeded
- Template validation
- CSV format validation

## Security

- OAuth 2.0 authentication
- Encrypted credential storage
- CSRF protection
- Input validation
- Session management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 

## CSV Upload Format

### Basic Example
```csv
template_name,name,email,company,position
Welcome_Template,John Doe,john.doe@gmail.com,ACME Inc,Software Engineer
```

### Required Fields
- `template_name`: Must match an existing template name
- `email`: Valid Gmail or Google Workspace email

### Optional Fields
- Any column that matches template placeholders
- Common fields: name, company, position, etc.

See [CSV Format Documentation](docs/csv_format.md) for detailed information. #   e m a i l - a u t o m a t i o n  
 