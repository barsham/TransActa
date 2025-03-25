"""
Security module for the SillyPostilion web portal.
Provides encryption, decryption, and audit logging functionality.
"""

import os
import logging
import json
import datetime
import uuid
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
from flask import request, session, current_app, g

# Configure logger
logger = logging.getLogger('security')
handler = logging.FileHandler('security.log')
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Audit logger 
audit_logger = logging.getLogger('audit')
audit_handler = logging.FileHandler('audit.log')
audit_handler.setFormatter(logging.Formatter('%(asctime)s [AUDIT] %(message)s'))
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

class SecurityManager:
    """Manages security features including encryption and audit logging."""
    
    def __init__(self, app=None):
        self.app = app
        
        # Generate/load encryption key
        self.encryption_key = os.environ.get('ENCRYPTION_KEY')
        if not self.encryption_key:
            # Generate a key if not provided
            self.encryption_key = Fernet.generate_key().decode('utf-8')
            logger.warning("No encryption key provided. Generated a temporary one.")
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the security manager with the Flask app."""
        self.app = app
        
        # Register before_request to log all requests
        app.before_request(self._log_request)
        
        # Register teardown_request to log responses
        app.teardown_request(self._log_response)
        
        # Add security manager to app context
        app.extensions['security_manager'] = self
    
    def _log_request(self):
        """Log information about the incoming request."""
        g.request_id = str(uuid.uuid4())
        g.request_start_time = datetime.datetime.now()
        
        client_ip = request.remote_addr
        path = request.path
        method = request.method
        user_agent = request.user_agent.string
        
        audit_logger.info(
            f"REQUEST | ID: {g.request_id} | IP: {client_ip} | "
            f"{method} {path} | User-Agent: {user_agent}"
        )
    
    def _log_response(self, exception=None):
        """Log information about the outgoing response."""
        if hasattr(g, 'request_id') and hasattr(g, 'request_start_time'):
            duration = datetime.datetime.now() - g.request_start_time
            status_code = getattr(response, 'status_code', 500 if exception else 200)
            
            audit_logger.info(
                f"RESPONSE | ID: {g.request_id} | "
                f"Status: {status_code} | Duration: {duration.total_seconds():.3f}s"
            )
            
            if exception:
                audit_logger.error(
                    f"EXCEPTION | ID: {g.request_id} | {str(exception)}"
                )
    
    def log_security_event(self, event_type, details):
        """Log a security-related event."""
        user_id = session.get('user_id', 'anonymous')
        client_ip = request.remote_addr if request else 'internal'
        
        event = {
            'timestamp': datetime.datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'client_ip': client_ip,
            'details': details
        }
        
        audit_logger.info(f"SECURITY EVENT | {json.dumps(event)}")
        return event
    
    def encrypt_data(self, data):
        """Encrypt sensitive data."""
        if not data:
            return None
            
        try:
            if isinstance(data, dict) or isinstance(data, list):
                data = json.dumps(data)
            
            if not isinstance(data, bytes):
                data = str(data).encode('utf-8')
            
            f = Fernet(self.encryption_key.encode('utf-8') if isinstance(self.encryption_key, str) else self.encryption_key)
            encrypted = f.encrypt(data)
            return b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            self.log_security_event('encryption_error', {'error': str(e)})
            return None
    
    def decrypt_data(self, encrypted_data):
        """Decrypt encrypted data."""
        if not encrypted_data:
            return None
            
        try:
            f = Fernet(self.encryption_key.encode('utf-8') if isinstance(self.encryption_key, str) else self.encryption_key)
            decrypted = f.decrypt(b64decode(encrypted_data))
            
            # Try to parse as JSON if possible
            try:
                return json.loads(decrypted)
            except:
                return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            self.log_security_event('decryption_error', {'error': str(e)})
            return None
    
    def hash_data(self, data):
        """Create a hash of data."""
        if not data:
            return None
            
        try:
            if not isinstance(data, bytes):
                data = str(data).encode('utf-8')
                
            digest = hashes.Hash(hashes.SHA256())
            digest.update(data)
            return digest.finalize().hex()
        except Exception as e:
            logger.error(f"Hashing error: {str(e)}")
            return None
    
    def verify_hash(self, data, hash_value):
        """Verify data against a hash."""
        calculated_hash = self.hash_data(data)
        return calculated_hash == hash_value
    
    def secure_headers(self):
        """Return a dictionary of security headers to apply to responses."""
        return {
            'Content-Security-Policy': "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' https://cdn.replit.com https://cdnjs.cloudflare.com",
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }


# Create an instance of the security manager
security_manager = SecurityManager()


# Add a helper function to get the security manager instance
def get_security_manager():
    """Return the security manager instance."""
    if hasattr(current_app, 'extensions') and 'security_manager' in current_app.extensions:
        return current_app.extensions['security_manager']
    return security_manager