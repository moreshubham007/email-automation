# Setup script for Windows
Write-Host "Starting Gmail Mail Merge App Setup..." -ForegroundColor Green

# Check Python version
$pythonVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$pythonVersion -lt [version]"3.7") {
    Write-Host "Error: Python 3.7 or higher is required (found $pythonVersion)" -ForegroundColor Red
    exit 1
}

# Create and activate virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv
.\venv\Scripts\Activate

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create necessary directories
Write-Host "Creating required directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "instance"
New-Item -ItemType Directory -Force -Path "client_secrets"
New-Item -ItemType Directory -Force -Path "logs"

# Create .env file if it doesn't exist
if (-not(Test-Path -Path ".env" -PathType Leaf)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    @"
# Flask configuration
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(16))")

# Database configuration
DATABASE_URL=sqlite:///instance/app.db

# Google OAuth 2.0 configuration
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5000/oauth2callback

# Email configuration
MAX_EMAILS_PER_DAY=2000
SMTP_RATE_LIMIT=250
"@ | Out-File -FilePath ".env" -Encoding UTF8
}

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
$env:FLASK_APP = "app"
flask db init
flask db migrate -m "initial migration"
flask db upgrade

Write-Host "`nSetup completed successfully!" -ForegroundColor Green
Write-Host "`nTo start the development server:"
Write-Host "1. Ensure virtual environment is activated: .\venv\Scripts\Activate"
Write-Host "2. Start the server: flask run"
Write-Host "`nMake sure to update the .env file with your Google OAuth credentials!" 