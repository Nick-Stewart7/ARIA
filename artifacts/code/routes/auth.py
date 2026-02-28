from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from ARIA.artifacts.code.models import User, Role
from ARIA.artifacts.code.forms import LoginForm, RegisterForm, PasswordChangeForm, ProfileForm
from ARIA.artifacts.code.app import db, bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('tasks.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Login user
            login_user(user, remember=form.remember_me.data)
            session.permanent = True
            
            flash(f'Welcome back, {user.username}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('tasks.dashboard'))
        
        flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html', title='Login', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('tasks.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Get default user role
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(name='user', description='Regular User')
            db.session.add(user_role)
            db.session.commit()
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            role_id=user_role.id
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.username
    logout_user()
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    form = ProfileForm(
        original_username=current_user.username,
        original_email=current_user.email
    )
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('auth/profile.html', title='Profile', form=form)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Current password is incorrect', 'danger')
    
    return render_template('auth/change_password.html', title='Change Password', form=form)

@auth_bp.route('/')
def index():
    """Home page"""
    if current_user.is_authenticated:
        return redirect(url_for('tasks.dashboard'))
    return redirect(url_for('auth.login'))