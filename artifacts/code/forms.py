from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, DateTimeLocalField
from wtforms.validators import DataRequired, Email, Length, ValidationError, EqualTo, Optional
from ARIA.artifacts.code.models import User

class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6)
    ])
    remember_me = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    
    def validate_username(self, username):
        """Check if username is already taken"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Check if email is already registered"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please choose a different one.')

class TaskForm(FlaskForm):
    """Task creation and editing form"""
    title = StringField('Title', validators=[
        DataRequired(),
        Length(min=1, max=200)
    ])
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=1000)
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='medium')
    due_date = DateTimeLocalField('Due Date', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    completed = BooleanField('Completed')

class PasswordChangeForm(FlaskForm):
    """Password change form"""
    current_password = PasswordField('Current Password', validators=[
        DataRequired()
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    new_password2 = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])

class ProfileForm(FlaskForm):
    """User profile editing form"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=80)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    
    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
    
    def validate_username(self, username):
        """Check if username is available (excluding current user)"""
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Check if email is available (excluding current user)"""
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email already registered. Please choose a different one.')