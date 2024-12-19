from app import create_app, db
from app.models import GmailAccount
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import json
import logging
from datetime import datetime
import sys
import time
from colorama import init, Fore, Style
import schedule
#pip install colorama
# Initialize colorama for colored output
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('force_token_refresh.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_status(message, status="", end='\n'):
    """Print colored status message"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Color coding for different status types
    status_colors = {
        "SUCCESS": Fore.GREEN + "✓" + Style.RESET_ALL,
        "FAILED": Fore.RED + "✗" + Style.RESET_ALL,
        "INFO": Fore.BLUE + "ℹ" + Style.RESET_ALL,
        "WARN": Fore.YELLOW + "!" + Style.RESET_ALL
    }
    
    status_symbol = status_colors.get(status, "")
    if status_symbol:
        print(f"[{timestamp}] {status_symbol} {message}", end=end)
    else:
        print(f"[{timestamp}] {message}", end=end)
    sys.stdout.flush()

def force_refresh_token(account, index=None, total=None):
    """Force refresh the access token for a Gmail account"""
    try:
        progress_info = f"({index}/{total}) " if index and total else ""
        print_status(f"{progress_info}Processing {account.email}... ", end='')
        
        # Load credentials from database
        creds_data = json.loads(account.credentials)
        credentials = Credentials(
            token=creds_data.get('token'),
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data.get('token_uri'),
            client_id=creds_data.get('client_id'),
            client_secret=creds_data.get('client_secret'),
            scopes=creds_data.get('scopes')
        )

        try:
            # Force refresh token
            print_status("Forcing token refresh... ", end='')
            credentials.refresh(Request())
            
            # Update credentials in database
            account.credentials = json.dumps({
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expiry': credentials.expiry.isoformat()
            })
            db.session.commit()
            print_status("Token refreshed successfully", status="SUCCESS")
            logger.info(f"Successfully refreshed token for {account.email}")
            return True
            
        except Exception as refresh_error:
            print_status(f"Failed to refresh token: {str(refresh_error)}", status="FAILED")
            logger.error(f"Error refreshing token for {account.email}: {str(refresh_error)}")
            return False
            
    except Exception as e:
        print_status(f"Error: {str(e)}", status="FAILED")
        logger.error(f"Error processing account {account.email}: {str(e)}")
        return False

def force_refresh_all_tokens():
    """Force refresh tokens for all authenticated Gmail accounts"""
    print_status("\n=== Starting Force Token Refresh Process ===\n", status="INFO")
    
    app = create_app()
    with app.app_context():
        # Get all authenticated accounts
        accounts = GmailAccount.query.filter_by(authenticated=True).all()
        total_accounts = len(accounts)
        print_status(f"Found {total_accounts} authenticated accounts\n", status="INFO")
        
        if total_accounts == 0:
            print_status("No authenticated accounts found. Exiting.", status="WARN")
            return
        
        # Initialize counters
        success_count = 0
        failed_count = 0
        
        # Process each account
        for index, account in enumerate(accounts, 1):
            try:
                if force_refresh_token(account, index, total_accounts):
                    success_count += 1
                else:
                    failed_count += 1
                    
                # Add a small delay between requests to avoid rate limiting
                if index < total_accounts:
                    time.sleep(1)
                    
            except Exception as e:
                failed_count += 1
                print_status(f"Unexpected error with {account.email}: {str(e)}", status="FAILED")
                logger.error(f"Failed to refresh token for {account.email}: {str(e)}")
        
        # Print summary
        print_status(f"""
=== Force Token Refresh Summary ===
Total accounts processed: {total_accounts}
Successfully refreshed:   {success_count}
Failed:                  {failed_count}
===============================
""", status="INFO")

def main():
    def job():
        start_time = datetime.now()
        logger.info("=== Starting scheduled token refresh job ===")
        print_status(f"Force token refresh process started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}", status="INFO")
        
        try:
            force_refresh_all_tokens()
        except Exception as e:
            print_status(f"\nCritical error: {str(e)}", status="FAILED")
            logger.critical(f"Critical error in refresh process: {str(e)}")
            return
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Job completed. Duration: {duration}")
        print_status(f"\nProcess completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}", status="INFO")
        print_status(f"Total duration: {duration}", status="INFO")
        logger.info("=== Scheduled job finished ===\n")

    # Schedule the job to run every 40 minutes
    schedule.every(40).minutes.do(job)
    
    # Log scheduler start
    logger.info("Scheduler initialized - Set to run every 40 minutes")
    print_status("Scheduler initialized - Will run every 40 minutes", status="INFO")
    
    # Run the job immediately once
    logger.info("Running initial job...")
    print_status("Running initial job...", status="INFO")
    job()
    
    # Calculate and show next run time
    next_run = schedule.next_run()
    logger.info(f"Next scheduled run at: {next_run}")
    print_status(f"Next scheduled run at: {next_run}", status="INFO")
    
    # Keep the script running and execute scheduled jobs
    print_status("Scheduler is running. Press Ctrl+C to stop.", status="INFO")
    while True:
        schedule.run_pending()
        time.sleep(1)
        
        # Update next run time every minute
        if int(time.time()) % 60 == 0:  # Every minute
            next_run = schedule.next_run()
            logger.info(f"Next scheduled run at: {next_run}")
            print_status(f"Next scheduled run at: {next_run}", status="INFO")

if __name__ == "__main__":
    try:
        logger.info("=== Script started ===")
        main()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        print_status("\nScheduler stopped by user.", status="INFO")
        sys.exit(0) 