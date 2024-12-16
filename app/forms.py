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
    email = StringField('Email Address', validators=[
        DataRequired(),
        Email(message='Must be a valid email address')
    ])
    description = TextAreaField('Description')

    def validate_email(self, field):
        """Custom validator for email addresses"""
        email = field.data.lower()
        
        # Basic email validation is already handled by the Email validator
        # No need for additional domain checks
        if not email:
            raise ValidationError('Email address is required.')

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
 