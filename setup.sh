#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Gmail Mail Merge App Setup...${NC}\n"

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$python_version < 3.7" | bc -l) )); then
    echo -e "${RED}Error: Python 3.7 or higher is required (found $python_version)${NC}"
    exit 1
fi

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Create necessary directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p instance
mkdir -p client_secrets
mkdir -p logs

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << EOL
# Flask configuration
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')

# Database configuration
DATABASE_URL=sqlite:///instance/app.db

# Google OAuth 2.0 configuration
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5000/oauth2callback

# Email configuration
MAX_EMAILS_PER_DAY=2000
SMTP_RATE_LIMIT=250
EOL
fi

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
export FLASK_APP=app
flask db upgrade

echo -e "\n${GREEN}Setup completed successfully!${NC}"
echo -e "\nTo start the development server:"
echo -e "1. Activate the virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "2. Start the server: ${YELLOW}flask run${NC}"
echo -e "\nMake sure to update the .env file with your Google OAuth credentials!" 