from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, BooleanField, IntegerField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Regexp, ValidationError, NumberRange
import re

class ClientSecretForm(FlaskForm):
    project_name = StringField('Project Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    client_secret = FileField('Client Secret JSON', validators=[
        FileRequired(),
        FileAllowed(['json'], 'JSON files only!')
    ])

class GmailIDsUploadForm(FlaskForm):
    project = SelectField('Project', coerce=int, validators=[DataRequired()])
    csv_file = FileField('CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'CSV files only!')
    ])

class TemplateForm(FlaskForm):
    name = StringField('Template Name', validators=[DataRequired()])
    subject = StringField('Email Subject', validators=[DataRequired()])
    description = TextAreaField('Description')
    content = TextAreaField('Content', validators=[DataRequired()])
    use_file = BooleanField('Upload HTML File Instead')
    html_file = FileField('HTML Template File')

class SingleGmailForm(FlaskForm):
    project = SelectField('Project', coerce=int, validators=[DataRequired()])
    email = StringField('Gmail Address', validators=[
        DataRequired(),
        Email(message='Must be a valid email address')
    ])
    description = TextAreaField('Description')

    def validate_email(self, field):
        """Custom validator for Google email addresses"""
        email = field.data.lower()
        
        # List of valid Google email domains
        google_domains = [
            'gmail.com',
            'googlemail.com',
            'google.com'
        ]
        
        # Check if it's a standard Gmail address
        domain = email.split('@')[-1]
        
        # Check if it's a Google Workspace domain
        is_google_workspace = False
        try:
            # You might want to add actual Google Workspace domain verification here
            # For now, we'll just check MX records
            import dns.resolver
            mx_records = dns.resolver.resolve(domain, 'MX')
            for mx in mx_records:
                if 'google' in str(mx.exchange).lower():
                    is_google_workspace = True
                    break
        except:
            pass

        if domain not in google_domains and not is_google_workspace:
            raise ValidationError('Must be a valid Google email address (Gmail or Google Workspace)')

class EmailSchedulerForm(FlaskForm):
    csv_file = FileField('Sender Accounts CSV', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'CSV files only!')
    ])
    min_delay = IntegerField('Minimum Delay', validators=[
        DataRequired(),
        NumberRange(min=0, message="Minimum delay must be non-negative")
    ])
    max_delay = IntegerField('Maximum Delay', validators=[
        DataRequired(),
        NumberRange(min=0, message="Maximum delay must be non-negative")
    ])

    def validate_max_delay(self, field):
        if field.data < self.min_delay.data:
            raise ValidationError('Maximum delay must be greater than or equal to minimum delay')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
 