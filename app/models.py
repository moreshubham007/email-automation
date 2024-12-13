from datetime import datetime
from app import db, login
import json
import re
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    client_secret_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    gmail_accounts = db.relationship('GmailAccount', backref='project', lazy=True)

    def get_oauth_credentials(self):
        """Get OAuth credentials for this project"""
        with open(self.client_secret_path) as f:
            return json.load(f)

class GmailAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    authenticated = db.Column(db.Boolean, default=False)
    credentials = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Template(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200))
    description = db.Column(db.Text)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_placeholders(self):
        """Get all placeholders from subject and content"""
        placeholders = set()
        if self.subject:
            placeholders.update(re.findall(r'{{(.*?)}}', self.subject))
        if self.content:
            placeholders.update(re.findall(r'{{(.*?)}}', self.content))
        return list(placeholders)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'description': self.description,
            'content': self.content,
            'type': self.type,
            'placeholders': self.get_placeholders()
        }

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return User.query.get(int(id))