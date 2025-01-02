import os
import sys

# Add the parent directory to Python path so we can import the app module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from app import create_app, db
from app.models import GmailAccount
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(current_dir, 'gmail_accounts_deletion.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_progress(message, end='\n'):
    """Print progress message with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", end=end)
    sys.stdout.flush()

def delete_gmail_accounts(dry_run=True):
    """Delete all Gmail accounts from the database"""
    print_progress("\n=== Starting Gmail Accounts Deletion Process ===\n")
    
    app = create_app()
    with app.app_context():
        try:
            # Get all Gmail accounts
            accounts = GmailAccount.query.all()
            total_accounts = len(accounts)
            
            print_progress(f"Found {total_accounts} Gmail accounts\n")
            
            if total_accounts == 0:
                print_progress("No Gmail accounts found. Exiting.")
                return
            
            # Print accounts that will be deleted
            print_progress("The following accounts will be deleted:")
            for account in accounts:
                print_progress(f"- {account.email} (Project ID: {account.project_id})")
            
            if dry_run:
                print_progress("\nDRY RUN - No accounts will be actually deleted")
                return
            
            # Confirm deletion
            confirmation = input("\nAre you sure you want to delete all Gmail accounts? This action cannot be undone! (yes/no): ")
            if confirmation.lower() != 'yes':
                print_progress("Deletion cancelled by user.")
                return
            
            # Delete accounts
            deleted_count = 0
            failed_count = 0
            
            for account in accounts:
                try:
                    print_progress(f"Deleting {account.email}... ", end='')
                    db.session.delete(account)
                    deleted_count += 1
                    print_progress("✓")
                    logger.info(f"Successfully deleted account: {account.email}")
                except Exception as e:
                    failed_count += 1
                    print_progress(f"✗ Error: {str(e)}")
                    logger.error(f"Failed to delete account {account.email}: {str(e)}")
            
            # Commit changes
            try:
                db.session.commit()
                print_progress("\nChanges committed to database successfully")
            except Exception as e:
                print_progress(f"\n❌ Error committing changes: {str(e)}")
                logger.error(f"Error committing changes: {str(e)}")
                db.session.rollback()
                return
            
            # Print summary
            print_progress(f"""
=== Deletion Summary ===
Total accounts found: {total_accounts}
Successfully deleted: {deleted_count}
Failed to delete:     {failed_count}
=====================
""")
            
        except Exception as e:
            print_progress(f"\n❌ Critical error: {str(e)}")
            logger.critical(f"Critical error in deletion process: {str(e)}")
            return 1

def main():
    """Main function with command line argument handling"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Delete all configured Gmail accounts')
    parser.add_argument('--dry-run', action='store_true', 
                      help='Perform a dry run without actually deleting accounts')
    args = parser.parse_args()
    
    start_time = datetime.now()
    print_progress(f"Deletion process started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        delete_gmail_accounts(dry_run=args.dry_run)
    except Exception as e:
        print_progress(f"\n❌ Critical error: {str(e)}")
        logger.critical(f"Critical error in deletion process: {str(e)}")
        return 1
    
    end_time = datetime.now()
    duration = end_time - start_time
    print_progress(f"\nProcess completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print_progress(f"Total duration: {duration}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 