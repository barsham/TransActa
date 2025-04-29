"""
Authentication routes for SillyPostilion

This module provides routes for user authentication,
including login, logout, and password management.
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash

from app import db
from models import User

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Setup logger
logger = logging.getLogger('auth_routes')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Find user by username
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Check if account is locked
            if not user.is_active:
                flash('Your account is locked. Please contact an administrator.', 'danger')
                return render_template('auth/login.html')
                
            # Log successful login
            user.log_login()
            db.session.commit()
            
            # Login the user
            login_user(user, remember=remember)
            logger.info(f"User '{user.username}' logged in")
            
            # Redirect to requested page or default
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
                
            flash('Login successful', 'success')
            return redirect(next_page)
        else:
            # Handle failed login
            if user:
                # Increment failed login count and potentially lock account
                user.failed_login_count += 1
                user.last_failed_login = datetime.utcnow()
                
                # Check if account should be locked
                if user.failed_login_count >= 5:  # TODO: Get from settings
                    user.lock_account()
                    logger.warning(f"Account '{user.username}' locked due to too many failed login attempts")
                    flash('Your account has been locked due to too many failed login attempts. Please contact an administrator.', 'danger')
                else:
                    logger.warning(f"Failed login attempt for user '{user.username}' (attempt {user.failed_login_count})")
                    flash('Invalid username or password', 'danger')
                    
                db.session.commit()
            else:
                logger.warning(f"Failed login attempt for unknown user '{username}'")
                flash('Invalid username or password', 'danger')
                
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    if current_user.is_authenticated:
        logger.info(f"User '{current_user.username}' logged out")
        
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile"""
    return render_template('auth/profile.html')

@auth_bp.route('/password-change', methods=['GET', 'POST'])
@login_required
def password_change():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match', 'danger')
        elif len(new_password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
        else:
            # Update password
            current_user.set_password(new_password)
            db.session.commit()
            
            logger.info(f"Password changed for user '{current_user.username}'")
            flash('Your password has been updated', 'success')
            return redirect(url_for('auth.profile'))
            
    return render_template('auth/password_change.html')

@auth_bp.route('/create-admin', methods=['GET', 'POST'])
def create_admin():
    """Create admin user if none exists"""
    # Check if an admin already exists
    admin_exists = User.query.filter_by(is_admin=True).first() is not None
    
    if admin_exists:
        flash('Admin user already exists', 'warning')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match', 'danger')
        elif len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
        else:
            # Create admin user
            admin = User(
                username=username,
                email=email,
                password=password,
                is_admin=True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            logger.info(f"Admin user '{username}' created")
            flash('Admin user created successfully', 'success')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/create_admin.html')
