from app import create_app, db
from app.models import Project, GmailAccount, Template, User
import os
import shutil

def recreate_database():
    print("\n=== Starting Complete Database Reset Process ===")
    
    # Get the base directory (flask_gmail_app folder)
    base_dir = os.path.abspath(os.path.dirname(__file__))
    
    try:
        # 1. Delete migrations folder
        migrations_path = os.path.join(base_dir, 'migrations')
        if os.path.exists(migrations_path):
            print("Removing existing migrations folder...")
            shutil.rmtree(migrations_path)
            print("✓ Migrations folder removed")

        # 2. Delete instance folder
        instance_path = os.path.join(base_dir, 'instance')
        if os.path.exists(instance_path):
            print("Removing instance folder...")
            shutil.rmtree(instance_path)
            print("✓ Instance folder removed")

        # 3. Create fresh instance directory
        print("Creating new instance directory...")
        os.makedirs(instance_path)
        print("✓ Instance directory created")

        # 4. Create Flask app and initialize database
        app = create_app()
        with app.app_context():
            print("\nInitializing new database...")
            # Drop all tables first
            db.drop_all()
            # Create all tables fresh
            db.create_all()
            print("✓ Database tables created")
            
            # 5. Create test data
            print("\nCreating initial data...")
            
            # Create admin user
            admin = User(
                username="admin",
                email="admin@example.com"
            )
            admin.set_password("admin123")
            db.session.add(admin)
            print("✓ Admin user created")
            
            # Create test project
            project = Project(
                name="Test Project",
                description="Test project for development",
                client_secret_path="path/to/client_secret.json"
            )
            db.session.add(project)
            print("✓ Test project created")
            
            # Create test Gmail accounts
            gmail_accounts = [
                GmailAccount(
                    email="test1@gmail.com",
                    description="Test Account 1",
                    project=project,
                    authenticated=False
                ),
                GmailAccount(
                    email="test2@gmail.com",
                    description="Test Account 2",
                    project=project,
                    authenticated=False
                )
            ]
            for account in gmail_accounts:
                db.session.add(account)
            print("✓ Test Gmail accounts created")
            
            # Create test templates
            templates = [
                Template(
                    name="Welcome Email",
                    subject="Welcome to {{company}}",
                    description="New employee welcome email",
                    type="created",
                    content="""
                    <div>Dear {{name}},</div>
                    <br>
                    <div>Welcome to {{company}}! We're excited to have you join us as {{position}}.</div>
                    <br>
                    <div>Best regards,<br>HR Team</div>
                    """
                ),
                Template(
                    name="Newsletter",
                    subject="{{company}} Newsletter - {{month}}",
                    description="Monthly newsletter template",
                    type="created",
                    content="""
                    <div>Hello {{name}},</div>
                    <br>
                    <div>Here's your monthly update from {{company}}.</div>
                    <br>
                    <div>Regards,<br>Newsletter Team</div>
                    """
                )
            ]
            for template in templates:
                db.session.add(template)
            print("✓ Test templates created")
            
            # Commit everything
            db.session.commit()
            
            # Print summary
            print("\nDatabase Summary:")
            print(f"Users: {User.query.count()}")
            print(f"Projects: {Project.query.count()}")
            print(f"Gmail Accounts: {GmailAccount.query.count()}")
            print(f"Templates: {Template.query.count()}")
            
            print("\n=== Database Reset Complete! ===")
            print("\nDefault Login:")
            print("Username: admin")
            print("Password: admin123")
            print("\nNext Steps:")
            print("1. Start the application with 'flask run'")
            print("2. Login with the admin credentials")
            print("3. Configure your Google Cloud project and update client_secret.json")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error during reset: {str(e)}")
        print("\nTrying to clean up...")
        try:
            # Cleanup attempt
            if os.path.exists(migrations_path):
                shutil.rmtree(migrations_path)
            if os.path.exists(instance_path):
                shutil.rmtree(instance_path)
        except Exception as cleanup_error:
            print(f"Cleanup error: {str(cleanup_error)}")
        print("\nPlease fix the error and try again.")
        return False

if __name__ == "__main__":
    # Ask for confirmation
    print("\n⚠️  WARNING: This will delete all data and completely reset the database!")
    print("This includes:")
    print("- All database tables and data")
    print("- Migration history")
    print("- Instance folder")
    confirm = input("\nAre you sure you want to continue? (y/N): ")
    
    if confirm.lower() == 'y':
        success = recreate_database()
        if success:
            print("\nReset complete! Start the application with 'flask run'")
    else:
        print("\nDatabase reset cancelled.") 