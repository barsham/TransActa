import logging
import os
from datetime import datetime
import uuid
from urllib.parse import urlparse, urljoin

from flask import (
    Blueprint, render_template, redirect, request, url_for, 
    flash, session, current_app, abort
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import User, db

# Configure logging
logger = logging.getLogger(__name__)

# Create auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# Helper function to check if a URL is safe for redirects
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    # If the user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Login successful
            login_user(user, remember=remember)
            
            # Update last login timestamp and login count
            user.last_login = datetime.utcnow()
            user.login_count += 1
            db.session.commit()
            
            # Log successful login
            logger.info(f"User '{username}' logged in successfully")
            
            # Redirect to the next page or dashboard
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('index')
            
            return redirect(next_page)
        else:
            # Login failed
            flash('Invalid username or password', 'danger')
            logger.warning(f"Failed login attempt for user '{username}'")
    
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout"""
    username = current_user.username
    logout_user()
    flash('You have been logged out', 'info')
    logger.info(f"User '{username}' logged out")
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    """Display user profile"""
    return render_template('auth/profile.html')


@auth_bp.route('/password-change', methods=['GET', 'POST'])
@login_required
def password_change():
    """Handle password change"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match', 'danger')
        elif len(new_password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
        else:
            # Update password
            current_user.password_hash = generate_password_hash(new_password)
            current_user.password_changed_at = datetime.utcnow()
            db.session.commit()
            
            flash('Password updated successfully', 'success')
            logger.info(f"User '{current_user.username}' changed their password")
            return redirect(url_for('auth.profile'))
    
    return render_template('auth/password_change.html')


@auth_bp.route('/create-admin', methods=['GET', 'POST'])
def create_admin():
    """Create initial admin user if none exists"""
    # Check if any admin users already exist
    admin_exists = User.query.filter_by(is_admin=True).first() is not None
    
    # If admin exists and the current user is not authenticated as an admin, deny access
    if admin_exists and (not current_user.is_authenticated or not current_user.is_admin):
        abort(403)  # Forbidden
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
        elif len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
        else:
            # Create new admin user
            new_admin = User(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                is_admin=True,
                created_at=datetime.utcnow(),
                is_active=True
            )
            
            db.session.add(new_admin)
            db.session.commit()
            
            flash('Admin user created successfully', 'success')
            logger.info(f"Admin user '{username}' created")
            
            # Log in the new admin
            login_user(new_admin)
            return redirect(url_for('index'))
    
    return render_template('auth/create_admin.html')
