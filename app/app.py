from flask import Flask, render_template, jsonify, request, send_file, flash, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, FileField
from wtforms.validators import DataRequired
import threading
import time
from datetime import datetime
import os
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///templates.db'
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key
db = SQLAlchemy(app)

# Global scheduler state
scheduler_state = {
    'status': 'stopped',  # stopped, running, paused, completed
    'current_count': 0,
    'total_count': 6,  # Total number of emails to send
    'total_sent': 0,
    'start_time': None,
    'pause_time': None,
    'is_cancelled': False,
    'thread': None
}

# Lock for thread-safe operations
scheduler_lock = threading.Lock()

def sending_task():
    while True:
        with scheduler_lock:
            # Check if cancelled
            if scheduler_state['is_cancelled']:
                scheduler_state['status'] = 'stopped'
                scheduler_state['current_count'] = 0
                break
            
            # Check if paused
            if scheduler_state['status'] == 'paused':
                time.sleep(1)
                continue
            
            # Check if completed
            if scheduler_state['current_count'] >= scheduler_state['total_count']:
                scheduler_state['status'] = 'completed'
                break
            
            # Process if running
            if scheduler_state['status'] == 'running':
                scheduler_state['current_count'] += 1
                scheduler_state['total_sent'] += 1
                time.sleep(1)  # Simulate sending delay

@app.route('/scheduler')
def scheduler():
    return render_template('scheduler.html', state=scheduler_state)

@app.route('/scheduler/start', methods=['POST'])
def start_scheduler():
    global scheduler_state
    with scheduler_lock:
        if scheduler_state['status'] in ['stopped', 'completed']:
            # Reset state
            scheduler_state['current_count'] = 0
            scheduler_state['status'] = 'running'
            scheduler_state['start_time'] = datetime.now()
            scheduler_state['is_cancelled'] = False
            scheduler_state['pause_time'] = None
            
            # Start new thread only if not already running
            if not scheduler_state['thread'] or not scheduler_state['thread'].is_alive():
                thread = threading.Thread(target=sending_task)
                thread.daemon = True
                thread.start()
                scheduler_state['thread'] = thread
            
            return jsonify({'status': 'started'})
    return jsonify({'status': scheduler_state['status']})

@app.route('/scheduler/pause', methods=['POST'])
def pause_scheduler():
    with scheduler_lock:
        current_status = scheduler_state['status']
        
        if current_status == 'running':
            scheduler_state['status'] = 'paused'
            scheduler_state['pause_time'] = datetime.now()
            return jsonify({'status': 'paused'})
        elif current_status == 'paused':
            scheduler_state['status'] = 'running'
            scheduler_state['pause_time'] = None
            return jsonify({'status': 'running'})
        
        return jsonify({'status': current_status})

@app.route('/scheduler/cancel', methods=['POST'])
def cancel_scheduler():
    with scheduler_lock:
        scheduler_state['is_cancelled'] = True
        scheduler_state['status'] = 'stopped'
        scheduler_state['current_count'] = 0
        scheduler_state['start_time'] = None
        scheduler_state['pause_time'] = None
        return jsonify({'status': 'cancelled'})

@app.route('/scheduler/status')
def get_status():
    with scheduler_lock:
        remaining = scheduler_state['total_count'] - scheduler_state['current_count']
        return jsonify({
            'status': scheduler_state['status'],
            'count': scheduler_state['current_count'],
            'total_sent': scheduler_state['total_sent'],
            'remaining': remaining,
            'total_senders': scheduler_state['total_count'],
            'start_time': scheduler_state['start_time'].isoformat() if scheduler_state['start_time'] else None,
            'pause_time': scheduler_state['pause_time'].isoformat() if scheduler_state['pause_time'] else None
        })

@app.route('/download-template/<int:template_id>')
def download_template(template_id):
    # Get template from database
    template = Template.query.get_or_404(template_id)
    
    # Assuming template.file_path contains the path to the stored template file
    file_path = template.file_path
    
    # Check if file exists
    if not os.path.exists(file_path):
        flash('Template file not found', 'error')
        return redirect(url_for('template_management'))
    
    # Return the file for download
    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"{template.name}.docx"
    )

# Add Template Form
class TemplateForm(FlaskForm):
    name = StringField('Template Name', validators=[DataRequired()])
    subject = StringField('Email Subject', validators=[DataRequired()])
    description = TextAreaField('Description')
    content = TextAreaField('Content', validators=[DataRequired()])
    use_file = BooleanField('Upload HTML File Instead')
    html_file = FileField('HTML Template File')

@app.route('/template-management', methods=['GET', 'POST'])
def template_management():
    form = TemplateForm()
    templates = Template.query.all()
    print("Rendering template:", 'template_management.html')
    return render_template('template_management.html', form=form, templates=templates)

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200))
    description = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_placeholders(self):
        import re
        placeholders = set()
        # Find placeholders in subject
        if self.subject:
            placeholders.update(re.findall(r'{{(.*?)}}', self.subject))
        # Find placeholders in content
        if self.content:
            placeholders.update(re.findall(r'{{(.*?)}}', self.content))
        return list(placeholders)

@app.route('/edit-template/<int:template_id>', methods=['POST'])
def edit_template(template_id):
    template = Template.query.get_or_404(template_id)
    data = request.json
    
    try:
        template.name = data.get('name', template.name)
        template.subject = data.get('subject', template.subject)
        template.description = data.get('description', template.description)
        template.content = data.get('content', template.content)
        
        db.session.commit()
        return jsonify({'message': 'Template updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/delete-template/<int:template_id>', methods=['POST'])
def delete_template(template_id):
    template = Template.query.get_or_404(template_id)
    
    try:
        db.session.delete(template)
        db.session.commit()
        return jsonify({'message': 'Template deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True) 