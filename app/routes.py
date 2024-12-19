from flask import Blueprint, render_template, jsonify, flash, redirect, url_for, request, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Project, GmailAccount, Template, User
from app.forms import ClientSecretForm, GmailIDsUploadForm, TemplateForm, SingleGmailForm, EmailSchedulerForm, LoginForm
from werkzeug.utils import secure_filename
import os
import re
import json
from app import db
import google_auth_oauthlib.flow
from flask import session
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import time
import threading
import csv
from io import StringIO
from app.websockets import send_to_all_clients, email_status, status_lock, logger
from datetime import datetime, timedelta
import threading
import queue
from werkzeug.urls import url_parse
from dotenv import load_dotenv

load_dotenv()

main = Blueprint('main', __name__)

@main.context_processor
def inject_theme_css():
    themes = ['basic', 'minion', 'batman', 'ironman']
    return dict(themes=themes)

def send_draft_emails(app, sender_emails, min_delay, max_delay):
    """Background task to send drafts with delays"""
    with app.app_context():
        try:
            total_sent = 0
            sender_count = len(sender_emails)
            threads = []
            
            # Create a thread for each sender
            for sender_email in sender_emails:
                thread = threading.Thread(
                    target=process_single_sender,
                    args=(app, sender_email, min_delay, max_delay)
                )
                thread.daemon = True
                threads.append(thread)
                
                # Initialize status for this sender
                with status_lock:
                    email_status[sender_email] = {
                        'drafts_sent': 0,
                        'total_drafts': 0,
                        'status': 'starting',
                        'next_send_time': None
                    }
            
            # Start all threads simultaneously
            for thread in threads:
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
                
        except Exception as e:
            send_to_all_clients({
                'type': 'log',
                'message': f"Background task error: {str(e)}",
                'level': 'danger'
            })

def process_single_sender(app, sender_email, min_delay, max_delay):
    """Process drafts for a single sender"""
    with app.app_context():
        try:
            # Check if stopped
            with status_lock:
                if email_status.get(sender_email, {}).get('status') == 'stopped':
                    return

            account = GmailAccount.query.filter_by(email=sender_email).first()
            if not account or not account.authenticated:
                send_to_all_clients({
                    'type': 'log',
                    'message': f"Account not found or not authenticated: {sender_email}",
                    'level': 'danger'
                })
                return

            try:
                # Load credentials
                creds_data = json.loads(account.credentials)
                credentials = Credentials(
                    token=creds_data['token'],
                    refresh_token=creds_data['refresh_token'],
                    token_uri=creds_data['token_uri'],
                    client_id=creds_data['client_id'],
                    client_secret=creds_data['client_secret'],
                    scopes=creds_data['scopes']
                )

                # Create Gmail API service
                service = build('gmail', 'v1', credentials=credentials)

                # Get all drafts
                drafts_response = service.users().drafts().list(userId='me').execute()
                drafts = drafts_response.get('drafts', [])
                
                if not drafts:
                    send_to_all_clients({
                        'type': 'log',
                        'message': f"No drafts found for {sender_email}",
                        'level': 'warning'
                    })
                    return

                total_drafts = len(drafts)
                drafts_sent = 0
                
                send_to_all_clients({
                    'type': 'log',
                    'message': f"Found {total_drafts} drafts for {sender_email}",
                    'level': 'info'
                })
                
                # Update status for this sender
                with status_lock:
                    email_status[sender_email].update({
                        'total_drafts': total_drafts,
                        'status': 'sending'
                    })
                
                for draft in drafts:
                    try:
                        # Check if stopped
                        with status_lock:
                            if email_status.get(sender_email, {}).get('status') == 'stopped':
                                return

                        # Get draft details and send
                        draft_detail = service.users().drafts().get(
                            userId='me', 
                            id=draft['id']
                        ).execute()
                        
                        service.users().drafts().send(
                            userId='me',
                            body={'id': draft['id']}
                        ).execute()
                        
                        drafts_sent += 1
                        
                        # Calculate next send time
                        delay = random.randint(min_delay, max_delay)
                        next_send_time = datetime.now() + timedelta(seconds=delay)
                        
                        # Update status
                        with status_lock:
                            email_status[sender_email].update({
                                'drafts_sent': drafts_sent,
                                'next_send_time': next_send_time.isoformat(),
                                'status': 'sending'
                            })
                        
                        # Send progress update
                        send_to_all_clients({
                            'type': 'progress',
                            'progress': {
                                'sender_email': sender_email,
                                'drafts_sent': drafts_sent,
                                'total_drafts': total_drafts,
                                'next_send_time': next_send_time.isoformat(),
                                'status': 'sending'
                            }
                        })
                        
                        if drafts_sent < total_drafts:
                            time.sleep(delay)
                            
                    except Exception as e:
                        send_to_all_clients({
                            'type': 'log',
                            'message': f"Error sending draft for {sender_email}: {str(e)}",
                            'level': 'danger'
                        })
                
                # Update final status
                with status_lock:
                    email_status[sender_email].update({
                        'status': 'completed',
                        'next_send_time': None
                    })
                
                send_to_all_clients({
                    'type': 'log',
                    'message': f"Completed sending all drafts for {sender_email}",
                    'level': 'success'
                })
                
            except Exception as e:
                send_to_all_clients({
                    'type': 'log',
                    'message': f"Error processing account {sender_email}: {str(e)}",
                    'level': 'danger'
                })
                
        except Exception as e:
            send_to_all_clients({
                'type': 'log',
                'message': f"Error in process_single_sender for {sender_email}: {str(e)}",
                'level': 'danger'
            })

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('main.login'))
            
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
        
    return render_template('login.html', form=form)

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/')
@login_required
def index():
    try:
        stats = {
            'total_senders': GmailAccount.query.count(),
            'authenticated_senders': GmailAccount.query.filter_by(authenticated=True).count(),
            'total_templates': Template.query.count(),
            'active_projects': Project.query.count(),
            'recent_templates': Template.query.order_by(Template.created_at.desc()).limit(5).all(),
            'recent_senders': GmailAccount.query.order_by(GmailAccount.created_at.desc()).limit(5).all()
        }
    except Exception:
        stats = {
            'total_senders': 0,
            'authenticated_senders': 0,
            'total_templates': 0,
            'active_projects': 0,
            'recent_templates': [],
            'recent_senders': []
        }
    
    return render_template('index.html', stats=stats)

@main.route('/gmail-management', methods=['GET', 'POST'])
@login_required
def gmail_management():
    client_secret_form = ClientSecretForm()
    gmail_ids_form = GmailIDsUploadForm()
    single_gmail_form = SingleGmailForm()
    
    # Handle project form submission
    if client_secret_form.validate_on_submit():
        try:
            # Create project directory
            project_dir = os.path.join(current_app.config['CLIENT_SECRETS_DIR'], 
                                     secure_filename(client_secret_form.project_name.data))
            os.makedirs(project_dir, exist_ok=True)
            
            # Save client secrets file
            client_secret_file = client_secret_form.client_secret.data
            filename = os.path.join(project_dir, 'client_secrets.json')
            client_secret_file.save(filename)
            
            # Create project
            project = Project(
                name=client_secret_form.project_name.data,
                description=client_secret_form.description.data,
                client_secret_path=filename
            )
            
            db.session.add(project)
            db.session.commit()
            
            flash('Project created successfully!', 'success')
            return redirect(url_for('main.gmail_management'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating project: {str(e)}', 'error')
    
    # Populate project choices for forms
    projects = Project.query.all()
    project_choices = [(p.id, p.name) for p in projects]
    gmail_ids_form.project.choices = project_choices
    single_gmail_form.project.choices = project_choices
    
    gmail_accounts = GmailAccount.query.all()
    
    return render_template('gmail_management.html',
                         client_secret_form=client_secret_form,
                         gmail_ids_form=gmail_ids_form,
                         single_gmail_form=single_gmail_form,
                         projects=projects,
                         gmail_accounts=gmail_accounts)

@main.route('/add-gmail-account', methods=['POST'])
@login_required
def add_gmail_account():
    form = SingleGmailForm()
    form.project.choices = [(p.id, p.name) for p in Project.query.all()]
    
    if form.validate_on_submit():
        try:
            # Check if email already exists
            if GmailAccount.query.filter_by(email=form.email.data).first():
                flash('This Gmail address is already registered.', 'error')
                return redirect(url_for('main.gmail_management'))
            
            account = GmailAccount(
                email=form.email.data,
                description=form.description.data,
                project_id=form.project.data
            )
            
            db.session.add(account)
            db.session.commit()
            flash('Gmail account added successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('Error adding Gmail account. Please try again.', 'error')
            print(f"Error: {str(e)}")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'error')
    
    return redirect(url_for('main.gmail_management'))

@main.route('/template-management', methods=['GET', 'POST'])
@login_required
def template_management():
    form = TemplateForm()
    
    if form.validate_on_submit():
        try:
            content = form.content.data
            
            # If using file upload and file is provided
            if form.use_file.data and form.html_file.data:
                content = form.html_file.data.read().decode('utf-8')
            
            template = Template(
                name=form.name.data,
                subject=form.subject.data,
                description=form.description.data,
                content=content,
                type="created"
            )
            
            db.session.add(template)
            db.session.commit()
            flash('Template created successfully!', 'success')
            return redirect(url_for('main.template_management'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating template: {str(e)}', 'error')
    
    templates = Template.query.order_by(Template.created_at.desc()).all()
    return render_template('template_management.html', form=form, templates=templates)

@main.route('/mail-merge')
@login_required
def mail_merge():
    templates_data = [t.to_dict() for t in Template.query.all()]
    gmail_accounts = GmailAccount.query.filter_by(authenticated=True).all()
    
    return render_template('mail_merge.html',
                         templates=templates_data,
                         gmail_accounts=gmail_accounts)

# API Routes
@main.route('/api/projects')
@login_required
def get_projects():
    projects = Project.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'gmail_accounts_count': len(p.gmail_accounts)
    } for p in projects])

@main.route('/api/templates/<int:template_id>', methods=['GET'])
@login_required
def get_template(template_id):
    template = Template.query.get_or_404(template_id)
    return jsonify({
        'id': template.id,
        'name': template.name,
        'subject': template.subject,
        'description': template.description,
        'content': template.content
    })

@main.route('/api/templates/<int:template_id>', methods=['PUT'])
@login_required
def update_template(template_id):
    template = Template.query.get_or_404(template_id)
    data = request.get_json()
    
    template.name = data['name']
    template.subject = data['subject']
    template.description = data['description']
    template.content = data['content']
    
    # Update placeholders
    subject_placeholders = set(re.findall(r'{{(.*?)}}', data['subject']))
    content_placeholders = set(re.findall(r'{{(.*?)}}', data['content']))
    all_placeholders = list(subject_placeholders | content_placeholders)
    template.placeholders = json.dumps(all_placeholders)
    
    db.session.commit()
    
    flash('Template updated successfully!', 'success')
    return jsonify({'message': 'Template updated successfully'})

@main.route('/api/templates/<int:template_id>', methods=['DELETE'])
@login_required
def delete_template(template_id):
    template = Template.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    
    flash('Template deleted successfully!', 'success')
    return jsonify({'message': 'Template deleted successfully'})

@main.route('/add-project', methods=['POST'])
def add_project():
    form = ClientSecretForm()
    if form.validate_on_submit():
        try:
            # Create project directory
            project_dir = os.path.join(current_app.config['CLIENT_SECRETS_DIR'], 
                                     secure_filename(form.project_name.data))
            os.makedirs(project_dir, exist_ok=True)
            
            # Save client secrets file
            client_secret_file = form.client_secret.data
            filename = os.path.join(project_dir, 'client_secrets.json')
            client_secret_file.save(filename)
            
            # Create project
            project = Project(
                name=form.project_name.data,
                description=form.description.data,
                client_secret_path=filename
            )
            
            db.session.add(project)
            db.session.commit()
            
            flash('Project created successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating project: {str(e)}', 'error')
            
    return redirect(url_for('main.gmail_management'))

@main.route('/authenticate/<int:account_id>')
@login_required
def authenticate_gmail(account_id):
    account = GmailAccount.query.get_or_404(account_id)
    project = account.project
    
    # Set up OAuth flow with proper error handling
    try:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            project.client_secret_path,
            scopes=['https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.compose']
        )
        
        # Get the redirect URI from environment or construct it
        if os.getenv('GOOGLE_OAUTH_REDIRECT_URI'):
            redirect_uri = os.getenv('GOOGLE_OAUTH_REDIRECT_URI')
        else:
            redirect_uri = url_for('main.oauth2callback', _external=True)
        
        flow.redirect_uri = redirect_uri
        
        # Store necessary data in session
        session['oauth_account_id'] = account_id
        session['oauth_redirect_uri'] = redirect_uri
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',  # Force consent screen to get refresh token
            state=os.urandom(16).hex()  # Add secure state parameter
        )
        
        session['oauth_state'] = state
        return redirect(authorization_url)
        
    except Exception as e:
        flash(f'Authentication setup failed: {str(e)}', 'error')
        return redirect(url_for('main.gmail_management'))

@main.route('/oauth2callback')
def oauth2callback():
    # Verify state and session data
    account_id = session.get('oauth_account_id')
    stored_state = session.get('oauth_state')
    
    if not account_id or not stored_state:
        flash('Authentication session expired or invalid', 'error')
        return redirect(url_for('main.gmail_management'))
    
    account = GmailAccount.query.get_or_404(account_id)
    
    try:
        # Recreate flow with stored state
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            account.project.client_secret_path,
            scopes=['https://www.googleapis.com/auth/gmail.send',
                   'https://www.googleapis.com/auth/gmail.compose'],
            state=stored_state
        )
        
        # Set the same redirect URI as in the initial request
        flow.redirect_uri = session.get('oauth_redirect_uri')
        
        # Fetch token with full URL including query parameters
        authorization_response = request.url
        if not request.is_secure:
            authorization_response = authorization_response.replace('http://', 'https://')
        
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        
        # Store credentials securely
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
        
        # Clear sensitive session data
        session.pop('oauth_account_id', None)
        session.pop('oauth_state', None)
        session.pop('oauth_redirect_uri', None)
        
        flash('Gmail account authenticated successfully!', 'success')
        return redirect(url_for('main.gmail_management'))
        
    except Exception as e:
        flash(f'Authentication failed: {str(e)}', 'error')
        return redirect(url_for('main.gmail_management'))

def create_gmail_draft(sender, recipient, subject, body):
    """Create a draft email using Gmail API"""
    try:
        # Load credentials
        creds_data = json.loads(sender.credentials)
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data['refresh_token'],
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=creds_data['scopes']
        )

        # Create Gmail API service
        service = build('gmail', 'v1', credentials=credentials)

        # Create message
        message = MIMEMultipart('alternative')
        message['to'] = recipient
        message['from'] = sender.email
        message['subject'] = subject

        # Attach HTML body
        html_part = MIMEText(body, 'html')
        message.attach(html_part)

        # Encode message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create draft
        draft = service.users().drafts().create(
            userId='me',
            body={
                'message': {
                    'raw': encoded_message
                }
            }
        ).execute()

        return True, None
    except Exception as e:
        return False, str(e)

@main.route('/api/mail-merge', methods=['POST'])
@login_required
def process_mail_merge():
    try:
        # Get CSV data and test mode flag
        csv_data = json.loads(request.form.get('csv_data', '[]'))
        test_mode = request.form.get('test_mode') == 'true'
        
        if not csv_data:
            raise ValueError("No CSV data provided")

        # Group records by template and sender
        groups = {}
        for record in csv_data:
            if not all(key in record for key in ['template_name', 'sender_email', 'email']):
                raise ValueError("Missing required fields in CSV")
            
            key = (record['template_name'], record['sender_email'])
            
            if key not in groups:
                # Get template
                template = Template.query.filter_by(name=record['template_name']).first()
                if not template:
                    raise ValueError(f"Template not found: {record['template_name']}")
                
                # Get sender
                sender = GmailAccount.query.filter_by(email=record['sender_email']).first()
                if not sender or not sender.authenticated:
                    raise ValueError(f"Sender not authenticated: {record['sender_email']}")
                
                groups[key] = {
                    'template': template,
                    'sender': sender,
                    'records': []
                }
            
            groups[key]['records'].append(record)

        if test_mode:
            # Generate preview
            previews = []
            for (template_name, sender_email), group in groups.items():
                template = group['template']
                for record in group['records'][:3]:  # Preview first 3
                    subject = template.subject
                    content = template.content
                    
                    # Replace placeholders
                    for key, value in record.items():
                        if key not in ['template_name', 'sender_email']:
                            subject = subject.replace(f'{{{{{key}}}}}', str(value))
                            content = content.replace(f'{{{{{key}}}}}', str(value))
                    
                    previews.append({
                        'template_name': template_name,
                        'sender_email': sender_email,
                        'recipient': record.get('email', 'No recipient specified'),
                        'subject': subject,
                        'content': content
                    })
            
            return jsonify({'preview': previews})
        else:
            # Process actual mail merge
            results = {
                'success': [],
                'failed': []
            }

            for (template_name, sender_email), group in groups.items():
                template = group['template']
                sender = group['sender']

                for record in group['records']:
                    try:
                        subject = template.subject
                        content = template.content
                        
                        # Replace placeholders
                        for key, value in record.items():
                            if key not in ['template_name', 'sender_email']:
                                subject = subject.replace(f'{{{{{key}}}}}', str(value))
                                content = content.replace(f'{{{{{key}}}}}', str(value))

                        # Create draft
                        success = create_gmail_draft(
                            sender=sender,
                            recipient=record['email'],
                            subject=subject,
                            body=content
                        )

                        if success:
                            results['success'].append({
                                'sender': sender_email,
                                'recipient': record['email']
                            })
                        else:
                            results['failed'].append({
                                'sender': sender_email,
                                'recipient': record['email'],
                                'error': 'Failed to create draft'
                            })

                    except Exception as e:
                        results['failed'].append({
                            'sender': sender_email,
                            'recipient': record['email'],
                            'error': str(e)
                        })

            return jsonify({
                'message': 'Mail merge completed',
                'results': results
            })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Mail merge error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

def create_gmail_draft(sender, recipient, subject, body):
    """Create a Gmail draft"""
    try:
        # Load credentials
        creds_data = json.loads(sender.credentials)
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data['refresh_token'],
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=[
                'https://www.googleapis.com/auth/gmail.compose',
                'https://www.googleapis.com/auth/gmail.modify'
            ]
        )

        # Create Gmail service
        service = build('gmail', 'v1', credentials=credentials)

        # Create message
        message = MIMEMultipart('alternative')
        message['to'] = recipient
        message['from'] = sender.email
        message['subject'] = subject

        # Add HTML content
        html_part = MIMEText(body, 'html')
        message.attach(html_part)

        # Encode message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Create draft
        draft = service.users().drafts().create(
            userId='me',
            body={
                'message': {
                    'raw': encoded_message
                }
            }
        ).execute()

        return True

    except Exception as e:
        logger.error(f"Error creating draft: {e}")
        return False

@main.route('/project-management', methods=['GET', 'POST'])
@login_required
def project_management():
    form = ClientSecretForm()
    
    if form.validate_on_submit():
        try:
            # Create project directory
            project_dir = os.path.join(current_app.config['CLIENT_SECRETS_DIR'], 
                                     secure_filename(form.project_name.data))
            os.makedirs(project_dir, exist_ok=True)
            
            # Save client secrets file
            client_secret_file = form.client_secret.data
            filename = os.path.join(project_dir, 'client_secrets.json')
            client_secret_file.save(filename)
            
            # Create project
            project = Project(
                name=form.project_name.data,
                description=form.description.data,
                client_secret_path=filename
            )
            
            db.session.add(project)
            db.session.commit()
            
            flash('Project created successfully!', 'success')
            return redirect(url_for('main.project_management'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating project: {str(e)}', 'error')
    
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('project_management.html', form=form, projects=projects)

@main.route('/api/projects/<int:project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify({
        'id': project.id,
        'name': project.name,
        'description': project.description
    })

@main.route('/api/projects/<int:project_id>/details', methods=['GET'])
@login_required
def get_project_details(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify({
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'created_at': project.created_at.isoformat(),
        'gmail_accounts': [{
            'id': acc.id,
            'email': acc.email,
            'authenticated': acc.authenticated,
            'created_at': acc.created_at.isoformat()
        } for acc in project.gmail_accounts]
    })

@main.route('/api/projects/<int:project_id>', methods=['PUT'])
@login_required
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    try:
        # Update basic info
        project.name = request.form['name']
        project.description = request.form['description']
        
        # Update client secrets if provided
        if 'client_secret' in request.files and request.files['client_secret']:
            client_secret_file = request.files['client_secret']
            filename = os.path.join(os.path.dirname(project.client_secret_path), 'client_secrets.json')
            client_secret_file.save(filename)
            project.client_secret_path = filename
        
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return jsonify({'message': 'Project updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@main.route('/api/projects/<int:project_id>', methods=['DELETE'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    try:
        # Delete client secrets file
        if os.path.exists(project.client_secret_path):
            os.remove(project.client_secret_path)
        
        # Delete project directory if empty
        project_dir = os.path.dirname(project.client_secret_path)
        if os.path.exists(project_dir) and not os.listdir(project_dir):
            os.rmdir(project_dir)
        
        db.session.delete(project)
        db.session.commit()
        
        flash('Project deleted successfully!', 'success')
        return jsonify({'message': 'Project deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400 

@main.route('/draft-counts')
@login_required
def draft_counts():
    gmail_accounts = GmailAccount.query.filter_by(authenticated=True).all()
    projects = Project.query.all()
    return render_template('draft_counts.html', 
                         gmail_accounts=gmail_accounts,
                         projects=projects)

@main.route('/api/gmail/<int:account_id>/draft-count')
@login_required
def get_draft_count(account_id):
    account = GmailAccount.query.get_or_404(account_id)
    
    try:
        # Load credentials
        creds_data = json.loads(account.credentials)
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data['refresh_token'],
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=creds_data['scopes']
        )

        # Create Gmail API service
        service = build('gmail', 'v1', credentials=credentials)

        # Get drafts list
        drafts = service.users().drafts().list(userId='me').execute()
        draft_count = len(drafts.get('drafts', []))

        return jsonify({'count': draft_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 400 

@main.route('/scheduler', methods=['GET', 'POST'])
@login_required
def scheduler():
    form = EmailSchedulerForm()
    
    if request.method == 'POST':
        try:
            # Set form.csrf_token.data
            form.csrf_token.data = request.form.get('csrf_token')
            
            if form.validate_on_submit():
                # Get CSV file from form
                csv_file = request.files.get('csv_file')
                if not csv_file:
                    return jsonify({'error': 'No CSV file provided'}), 400

                # Read CSV content
                csv_content = csv_file.read().decode('utf-8')
                csv_reader = csv.DictReader(StringIO(csv_content))
                
                # Extract unique sender emails
                sender_emails = set()
                for row in csv_reader:
                    if 'sender_email' in row and row['sender_email'].strip():
                        sender_emails.add(row['sender_email'].strip())

                if not sender_emails:
                    return jsonify({'error': 'No valid sender emails found in CSV'}), 400

                # Get delay values
                min_delay = form.min_delay.data or 30
                max_delay = form.max_delay.data or 60

                # Clear previous status
                with status_lock:
                    email_status.clear()

                # Start background thread
                thread = threading.Thread(
                    target=send_draft_emails,
                    args=(
                        current_app._get_current_object(),
                        list(sender_emails),
                        min_delay,
                        max_delay
                    )
                )
                thread.daemon = True
                thread.start()

                send_to_all_clients({
                    'type': 'log',
                    'message': 'Sending process started',
                    'level': 'info'
                })

                return jsonify({'status': 'success'})
            else:
                logger.error(f"Form validation errors: {form.errors}")
                return jsonify({'error': 'Invalid form data', 'details': form.errors}), 400

        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            return jsonify({'error': str(e)}), 500
    
    return render_template('scheduler.html', form=form)

@main.route('/scheduler/start', methods=['POST'])
@login_required
def start_scheduler():
    try:
        form = EmailSchedulerForm()
        # Set form.csrf_token.data
        form.csrf_token.data = request.form.get('csrf_token')
        
        if form.validate_on_submit():
            # Get CSV file from form
            csv_file = request.files.get('csv_file')
            if not csv_file:
                return jsonify({'error': 'No CSV file provided'}), 400

            # Read CSV content
            csv_content = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(csv_content))
            
            # Extract unique sender emails
            sender_emails = set()
            for row in csv_reader:
                if 'sender_email' in row and row['sender_email'].strip():
                    sender_emails.add(row['sender_email'].strip())

            if not sender_emails:
                return jsonify({'error': 'No valid sender emails found in CSV'}), 400

            # Get delay values
            min_delay = form.min_delay.data or 30
            max_delay = form.max_delay.data or 60

            # Clear previous status
            with status_lock:
                email_status.clear()

            # Start background thread
            thread = threading.Thread(
                target=send_draft_emails,
                args=(
                    current_app._get_current_object(),
                    list(sender_emails),
                    min_delay,
                    max_delay
                )
            )
            thread.daemon = True
            thread.start()

            send_to_all_clients({
                'type': 'log',
                'message': 'Sending process started',
                'level': 'info'
            })

            return jsonify({'status': 'success'})
        else:
            logger.error(f"Form validation errors: {form.errors}")
            return jsonify({'error': 'Invalid form data', 'details': form.errors}), 400

    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        return jsonify({'error': str(e)}), 500 

@main.route('/scheduler/stop', methods=['POST'])
@login_required
def stop_scheduler():
    try:
        # Set cancelled flag in email status
        with status_lock:
            for sender_email in email_status:
                email_status[sender_email]['status'] = 'stopped'
        
        send_to_all_clients({
            'type': 'log',
            'message': 'Sending process stopped by user',
            'level': 'warning'
        })
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        return jsonify({'error': str(e)}), 500 

@main.route('/static/sounds/error.mp3')
def fallback_error_sound():
    return send_from_directory(
        os.path.join(current_app.root_path, 'static', 'sounds', 'global'),
        'crash.mp3'
    )

@main.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(current_app.root_path, 'static', 'images'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    ) 

@main.route('/delete-gmail-account/<int:account_id>', methods=['POST'])
@login_required
def delete_gmail_account(account_id):
    try:
        account = GmailAccount.query.get_or_404(account_id)
        email = account.email  # Store email for flash message
        
        # Delete the account
        db.session.delete(account)
        db.session.commit()
        
        flash(f'Gmail account {email} deleted successfully!', 'success')
        return redirect(url_for('main.gmail_management'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting Gmail account: {str(e)}', 'error')
        return redirect(url_for('main.gmail_management')) 

@main.route('/api/gmail/<int:account_id>/drafts', methods=['DELETE'])
@login_required
def delete_drafts(account_id):
    try:
        account = GmailAccount.query.get_or_404(account_id)
        
        # Load credentials
        creds_data = json.loads(account.credentials)
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data['refresh_token'],
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=creds_data['scopes']
        )

        # Create Gmail API service
        service = build('gmail', 'v1', credentials=credentials)

        # Get all drafts
        drafts_response = service.users().drafts().list(userId='me').execute()
        drafts = drafts_response.get('drafts', [])

        # Delete each draft
        for draft in drafts:
            service.users().drafts().delete(userId='me', id=draft['id']).execute()

        return jsonify({
            'success': True,
            'message': f'Successfully deleted {len(drafts)} drafts'
        })

    except Exception as e:
        logger.error(f"Error deleting drafts: {e}")
        return jsonify({
            'error': str(e)
        }), 500 