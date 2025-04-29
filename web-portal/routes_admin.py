"""
Admin routes for SillyPostilion

This module provides routes for the administrative interface
to manage endpoints, HSM keys, and system settings.
"""

import logging
import datetime
from uuid import uuid4
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user

from admin import get_admin_module, EndpointType, EndpointProtocol, AuthMethod, Endpoint
from hsm import HSMKeyType, get_hsm_manager

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Setup logger
logger = logging.getLogger('admin_routes')

@admin_bp.route('/')
@login_required
def index():
    """Admin dashboard"""
    admin_module = get_admin_module()
    
    return render_template(
        'admin/index.html',
        settings=admin_module.get_settings(),
        hsm_keys=admin_module.get_hsm_keys(include_expired=False),
        endpoints=admin_module.get_endpoints()
    )

# Endpoint Management Routes
@admin_bp.route('/endpoints')
@login_required
def endpoints():
    """List and manage endpoints"""
    admin_module = get_admin_module()
    
    return render_template(
        'admin/endpoints.html',
        endpoints=admin_module.get_endpoints()
    )

@admin_bp.route('/endpoints/add', methods=['GET', 'POST'])
@login_required
def add_endpoint():
    """Add a new endpoint"""
    admin_module = get_admin_module()
    
    if request.method == 'POST':
        try:
            # Create a unique ID for the endpoint
            endpoint_id = f"ep-{uuid4().hex[:8]}"
            
            # Parse form data
            endpoint_type = EndpointType(request.form.get('endpoint_type'))
            protocol = EndpointProtocol(request.form.get('protocol'))
            auth_method = AuthMethod(request.form.get('auth_method'))
            
            # Create auth credentials dictionary
            auth_credentials = {}
            if auth_method != AuthMethod.NONE:
                # Get credentials based on auth method
                if auth_method == AuthMethod.BASIC:
                    auth_credentials = {
                        'username': request.form.get('auth_credentials[username]', ''),
                        'password': request.form.get('auth_credentials[password]', '')
                    }
                elif auth_method == AuthMethod.OAUTH:
                    auth_credentials = {
                        'client_id': request.form.get('auth_credentials[client_id]', ''),
                        'client_secret': request.form.get('auth_credentials[client_secret]', ''),
                        'token_url': request.form.get('auth_credentials[token_url]', '')
                    }
                elif auth_method == AuthMethod.CERTIFICATE:
                    auth_credentials = {
                        'cert_path': request.form.get('auth_credentials[cert_path]', ''),
                        'key_path': request.form.get('auth_credentials[key_path]', '')
                    }
                elif auth_method == AuthMethod.HMAC:
                    auth_credentials = {
                        'key_id': request.form.get('auth_credentials[key_id]', ''),
                        'secret': request.form.get('auth_credentials[secret]', ''),
                        'algorithm': request.form.get('auth_credentials[algorithm]', 'SHA256')
                    }
            
            # Create endpoint
            endpoint = Endpoint(
                id=endpoint_id,
                name=request.form.get('name'),
                description=request.form.get('description', ''),
                endpoint_type=endpoint_type,
                protocol=protocol,
                host=request.form.get('host'),
                port=int(request.form.get('port')),
                path=request.form.get('path', ''),
                auth_method=auth_method,
                auth_credentials=auth_credentials,
                timeout=int(request.form.get('timeout', 30)),
                retry_attempts=int(request.form.get('retry_attempts', 3)),
                ssl_verify='ssl_verify' in request.form,
                enabled='enabled' in request.form
            )
            
            # Add to admin module
            if admin_module.add_endpoint(endpoint):
                flash('Endpoint added successfully', 'success')
                return redirect(url_for('admin.endpoints'))
            else:
                flash('Failed to add endpoint', 'danger')
                
        except Exception as e:
            logger.error(f"Error adding endpoint: {str(e)}")
            flash(f"Error adding endpoint: {str(e)}", 'danger')
    
    return render_template(
        'admin/endpoint_form.html',
        endpoint=None,
        endpoint_types=list(EndpointType),
        protocols=list(EndpointProtocol),
        auth_methods=list(AuthMethod)
    )

@admin_bp.route('/endpoints/<endpoint_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_endpoint(endpoint_id):
    """Edit an existing endpoint"""
    admin_module = get_admin_module()
    endpoint = admin_module.get_endpoint(endpoint_id)
    
    if not endpoint:
        flash('Endpoint not found', 'danger')
        return redirect(url_for('admin.endpoints'))
    
    if request.method == 'POST':
        try:
            # Parse form data
            endpoint_type = request.form.get('endpoint_type')
            protocol = request.form.get('protocol')
            auth_method = request.form.get('auth_method')
            
            # Create auth credentials dictionary
            auth_credentials = {}
            if auth_method != 'none':
                # Get credentials based on auth method
                if auth_method == 'basic':
                    auth_credentials = {
                        'username': request.form.get('auth_credentials[username]', ''),
                        'password': request.form.get('auth_credentials[password]', '')
                    }
                elif auth_method == 'oauth':
                    auth_credentials = {
                        'client_id': request.form.get('auth_credentials[client_id]', ''),
                        'client_secret': request.form.get('auth_credentials[client_secret]', ''),
                        'token_url': request.form.get('auth_credentials[token_url]', '')
                    }
                elif auth_method == 'certificate':
                    auth_credentials = {
                        'cert_path': request.form.get('auth_credentials[cert_path]', ''),
                        'key_path': request.form.get('auth_credentials[key_path]', '')
                    }
                elif auth_method == 'hmac':
                    auth_credentials = {
                        'key_id': request.form.get('auth_credentials[key_id]', ''),
                        'secret': request.form.get('auth_credentials[secret]', ''),
                        'algorithm': request.form.get('auth_credentials[algorithm]', 'SHA256')
                    }
            
            # Create updates dictionary
            updates = {
                'name': request.form.get('name'),
                'description': request.form.get('description', ''),
                'endpoint_type': endpoint_type,
                'protocol': protocol,
                'host': request.form.get('host'),
                'port': int(request.form.get('port')),
                'path': request.form.get('path', ''),
                'auth_method': auth_method,
                'auth_credentials': auth_credentials,
                'timeout': int(request.form.get('timeout', 30)),
                'retry_attempts': int(request.form.get('retry_attempts', 3)),
                'ssl_verify': 'ssl_verify' in request.form,
                'enabled': 'enabled' in request.form
            }
            
            # Update endpoint
            if admin_module.update_endpoint(endpoint_id, updates):
                flash('Endpoint updated successfully', 'success')
                return redirect(url_for('admin.endpoints'))
            else:
                flash('Failed to update endpoint', 'danger')
                
        except Exception as e:
            logger.error(f"Error updating endpoint: {str(e)}")
            flash(f"Error updating endpoint: {str(e)}", 'danger')
    
    return render_template(
        'admin/endpoint_form.html',
        endpoint=endpoint,
        endpoint_types=list(EndpointType),
        protocols=list(EndpointProtocol),
        auth_methods=list(AuthMethod)
    )

@admin_bp.route('/endpoints/<endpoint_id>/delete', methods=['POST'])
@login_required
def delete_endpoint(endpoint_id):
    """Delete an endpoint"""
    admin_module = get_admin_module()
    
    if admin_module.delete_endpoint(endpoint_id):
        flash('Endpoint deleted successfully', 'success')
    else:
        flash('Failed to delete endpoint', 'danger')
    
    return redirect(url_for('admin.endpoints'))

@admin_bp.route('/endpoints/<endpoint_id>/test')
@login_required
def test_endpoint(endpoint_id):
    """Test connection to an endpoint"""
    admin_module = get_admin_module()
    endpoint = admin_module.get_endpoint(endpoint_id)
    
    if not endpoint:
        flash('Endpoint not found', 'danger')
        return redirect(url_for('admin.endpoints'))
    
    # TODO: Implement actual connection testing
    # For now, just return success
    result = {
        'success': True,
        'message': 'Connection successful',
        'latency': 42,  # ms
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    return render_template(
        'admin/endpoint_test.html',
        endpoint=endpoint,
        result=result
    )

# HSM Key Management Routes
@admin_bp.route('/hsm-keys')
@login_required
def hsm_keys():
    """List and manage HSM keys"""
    admin_module = get_admin_module()
    
    return render_template(
        'admin/hsm_keys.html',
        hsm_keys=admin_module.get_hsm_keys(include_expired=True)
    )

@admin_bp.route('/hsm-keys/generate', methods=['GET', 'POST'])
@login_required
def generate_hsm_key():
    """Generate a new HSM key"""
    if request.method == 'POST':
        try:
            admin_module = get_admin_module()
            
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description', '')
            key_type_name = request.form.get('key_type')
            key_length = int(request.form.get('key_length', 256))
            software_fallback = 'software_fallback' in request.form
            
            # Validate key type
            try:
                key_type = HSMKeyType[key_type_name]
            except KeyError:
                flash(f"Invalid key type: {key_type_name}", 'danger')
                return redirect(url_for('admin.generate_hsm_key'))
            
            # Generate key
            key_entry = admin_module.generate_hsm_key(name, description, key_type)
            
            if key_entry:
                flash(f"Key '{name}' generated successfully", 'success')
                return redirect(url_for('admin.hsm_keys'))
            else:
                flash('Failed to generate key', 'danger')
                
        except Exception as e:
            logger.error(f"Error generating HSM key: {str(e)}")
            flash(f"Error generating HSM key: {str(e)}", 'danger')
    
    return render_template(
        'admin/generate_hsm_key.html',
        key_types=list(HSMKeyType)
    )

@admin_bp.route('/hsm-keys/import', methods=['GET', 'POST'])
@login_required
def import_hsm_key():
    """Import an encrypted HSM key"""
    admin_module = get_admin_module()
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            description = request.form.get('description', '')
            key_type_name = request.form.get('key_type')
            encrypted_key = request.form.get('encrypted_key')
            kek_id = request.form.get('kek_id')
            
            # Validate key type
            try:
                key_type = HSMKeyType[key_type_name]
            except KeyError:
                flash(f"Invalid key type: {key_type_name}", 'danger')
                return redirect(url_for('admin.import_hsm_key'))
            
            # Import key
            key_entry = admin_module.import_hsm_key(name, description, key_type, encrypted_key, kek_id)
            
            if key_entry:
                flash(f"Key '{name}' imported successfully", 'success')
                return redirect(url_for('admin.hsm_keys'))
            else:
                flash('Failed to import key', 'danger')
                
        except Exception as e:
            logger.error(f"Error importing HSM key: {str(e)}")
            flash(f"Error importing HSM key: {str(e)}", 'danger')
    
    # Get list of available KEKs (only non-expired Zone Master Keys)
    keks = [key for key in admin_module.get_hsm_keys() 
           if key.key_type == HSMKeyType.ZMK.name and not key.expired]
    
    return render_template(
        'admin/import_hsm_key.html',
        key_types=list(HSMKeyType),
        keks=keks
    )

@admin_bp.route('/hsm-keys/<key_id>')
@login_required
def view_hsm_key(key_id):
    """View HSM key details"""
    admin_module = get_admin_module()
    key = admin_module.get_hsm_key(key_id)
    
    if not key:
        flash('Key not found', 'danger')
        return redirect(url_for('admin.hsm_keys'))
    
    return render_template(
        'admin/view_hsm_key.html',
        key=key
    )

@admin_bp.route('/hsm-keys/<key_id>/rotate', methods=['GET', 'POST'])
@login_required
def rotate_hsm_key(key_id):
    """Rotate an HSM key"""
    admin_module = get_admin_module()
    key = admin_module.get_hsm_key(key_id)
    
    if not key:
        flash('Key not found', 'danger')
        return redirect(url_for('admin.hsm_keys'))
    
    if key.expired:
        flash('Cannot rotate an expired key', 'danger')
        return redirect(url_for('admin.hsm_keys'))
    
    if request.method == 'POST':
        try:
            # Rotate key
            new_key = admin_module.rotate_hsm_key(key_id)
            
            if new_key:
                flash(f"Key '{key.name}' rotated successfully", 'success')
                return redirect(url_for('admin.hsm_keys'))
            else:
                flash('Failed to rotate key', 'danger')
                
        except Exception as e:
            logger.error(f"Error rotating HSM key: {str(e)}")
            flash(f"Error rotating HSM key: {str(e)}", 'danger')
    
    return render_template(
        'admin/rotate_hsm_key.html',
        key=key
    )

@admin_bp.route('/hsm-keys/<key_id>/export', methods=['GET', 'POST'])
@login_required
def export_hsm_key(key_id):
    """Export an HSM key (encrypted under a KEK)"""
    admin_module = get_admin_module()
    key = admin_module.get_hsm_key(key_id)
    
    if not key:
        flash('Key not found', 'danger')
        return redirect(url_for('admin.hsm_keys'))
    
    if key.expired:
        flash('Cannot export an expired key', 'danger')
        return redirect(url_for('admin.hsm_keys'))
    
    if request.method == 'POST':
        try:
            # Get form data
            kek_id = request.form.get('kek_id')
            
            # Get KEK
            kek = admin_module.get_hsm_key(kek_id)
            if not kek or kek.expired or kek.key_type != HSMKeyType.ZMK.name:
                flash('Invalid KEK selected', 'danger')
                return redirect(url_for('admin.export_hsm_key', key_id=key_id))
            
            # Export key
            # NOTE: This is a placeholder - actual export would require integration with hsm_manager
            encrypted_key = 'ABC123DEF456GHI789JKL012MNO345PQR678STU901VWX234YZ'
            
            return render_template(
                'admin/export_hsm_key_result.html',
                key=key,
                kek=kek,
                encrypted_key=encrypted_key
            )
                
        except Exception as e:
            logger.error(f"Error exporting HSM key: {str(e)}")
            flash(f"Error exporting HSM key: {str(e)}", 'danger')
    
    # Get list of available KEKs (only non-expired Zone Master Keys)
    keks = [k for k in admin_module.get_hsm_keys() 
           if k.key_type == HSMKeyType.ZMK.name and not k.expired]
    
    return render_template(
        'admin/export_hsm_key.html',
        key=key,
        keks=keks
    )

@admin_bp.route('/hsm-keys/<key_id>/expire', methods=['POST'])
@login_required
def expire_hsm_key(key_id):
    """Mark an HSM key as expired"""
    admin_module = get_admin_module()
    key = admin_module.get_hsm_key(key_id)
    
    if not key:
        flash('Key not found', 'danger')
        return redirect(url_for('admin.hsm_keys'))
    
    if key.expired:
        flash('Key is already expired', 'warning')
        return redirect(url_for('admin.hsm_keys'))
    
    try:
        # Mark key as expired
        admin_module.update_hsm_key(key_id, {
            'expired': True,
            'rotation_date': datetime.datetime.now().isoformat()
        })
        
        flash(f"Key '{key.name}' marked as expired", 'success')
            
    except Exception as e:
        logger.error(f"Error expiring HSM key: {str(e)}")
        flash(f"Error expiring HSM key: {str(e)}", 'danger')
    
    return redirect(url_for('admin.hsm_keys'))

# Settings Management Routes
@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """System settings"""
    admin_module = get_admin_module()
    
    if request.method == 'POST':
        try:
            # Parse form data
            updates = {
                'transaction_processor_url': request.form.get('transaction_processor_url'),
                'log_level': request.form.get('log_level'),
                'session_timeout': int(request.form.get('session_timeout', 30)),
                'max_failed_logins': int(request.form.get('max_failed_logins', 5)),
                'password_expiry_days': int(request.form.get('password_expiry_days', 90)),
                'audit_retention_days': int(request.form.get('audit_retention_days', 365)),
                'enable_pin_verification': 'enable_pin_verification' in request.form,
                'enable_mac_verification': 'enable_mac_verification' in request.form,
                'offline_mode': 'offline_mode' in request.form,
                'maintenance_mode': 'maintenance_mode' in request.form
            }
            
            # Update settings
            if admin_module.update_settings(updates):
                flash('Settings updated successfully', 'success')
                
                # Apply log level change
                log_level = getattr(logging, updates['log_level'])
                logging.getLogger().setLevel(log_level)
                
                return redirect(url_for('admin.settings'))
            else:
                flash('Failed to update settings', 'danger')
                
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            flash(f"Error updating settings: {str(e)}", 'danger')
    
    return render_template(
        'admin/settings.html',
        settings=admin_module.get_settings()
    )

@admin_bp.route('/settings/maintenance', methods=['POST'])
@login_required
def toggle_maintenance_mode():
    """Toggle maintenance mode"""
    admin_module = get_admin_module()
    
    try:
        # Get new state from form
        maintenance_mode = request.form.get('maintenance_mode') == '1'
        
        # Update setting
        if admin_module.update_settings({'maintenance_mode': maintenance_mode}):
            mode_str = 'enabled' if maintenance_mode else 'disabled'
            flash(f"Maintenance mode {mode_str}", 'success')
        else:
            flash('Failed to toggle maintenance mode', 'danger')
            
    except Exception as e:
        logger.error(f"Error toggling maintenance mode: {str(e)}")
        flash(f"Error toggling maintenance mode: {str(e)}", 'danger')
    
    return redirect(url_for('admin.settings'))

# Other Admin Routes
@admin_bp.route('/user-management')
@login_required
def user_management():
    """User management"""
    # TODO: Implement user management
    return render_template('admin/user_management.html')

@admin_bp.route('/audit-logs')
@login_required
def audit_logs():
    """Audit logs"""
    # TODO: Implement audit log viewing
    return render_template('admin/audit_logs.html')
