from datetime import datetime
import logging
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
from flask import current_app

# Add audit logger for database operations
audit_logger = logging.getLogger('audit')
if not audit_logger.handlers:
    audit_handler = logging.FileHandler('audit.log')
    audit_handler.setFormatter(logging.Formatter('%(asctime)s [AUDIT] %(message)s'))
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)

class Transaction(db.Model):
    """
    Model for storing transaction data fetched from the Java backend
    This is used for caching data from the transaction processor
    
    Sensitive fields are encrypted before storage:
    - amount: Transaction amount (encrypted)
    - terminal_id: Terminal identifier (encrypted)
    - merchant_id: Merchant identifier (encrypted)
    - raw_message: Complete transaction message (encrypted)
    """
    id = db.Column(db.String(50), primary_key=True)
    mti = db.Column(db.String(4))
    processing_code = db.Column(db.String(6))
    # Encrypted fields
    _amount = db.Column(db.Text, name="amount")  # Encrypted
    transmission_datetime = db.Column(db.String(10))
    stan = db.Column(db.String(6))
    rrn = db.Column(db.String(12))
    response_code = db.Column(db.String(2))
    _terminal_id = db.Column(db.Text, name="terminal_id")  # Encrypted
    _merchant_id = db.Column(db.Text, name="merchant_id")  # Encrypted
    direction = db.Column(db.String(10))
    _raw_message = db.Column(db.Text, name="raw_message")  # Encrypted
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, nullable=True)
    access_count = db.Column(db.Integer, default=0)
    hash_value = db.Column(db.String(64), nullable=True)  # SHA-256 hash for integrity checks
    
    def __init__(self, **kwargs):
        """Initialize transaction with encryption for sensitive fields."""
        # Extract sensitive fields for encryption
        self.amount = kwargs.pop('amount', None)
        self.terminal_id = kwargs.pop('terminal_id', None)
        self.merchant_id = kwargs.pop('merchant_id', None)
        self.raw_message = kwargs.pop('raw_message', None)
        
        # Pass remaining fields to parent constructor
        super(Transaction, self).__init__(**kwargs)
        
        # Log creation
        audit_logger.info(f"TRANSACTION:CREATE | ID: {self.id} | MTI: {self.mti}")
    
    @property
    def amount(self):
        """Decrypt amount field."""
        if hasattr(current_app, 'extensions') and 'security_manager' in current_app.extensions:
            security_manager = current_app.extensions['security_manager']
            if self._amount:
                return security_manager.decrypt_data(self._amount)
        return self._amount
    
    @amount.setter
    def amount(self, value):
        """Encrypt amount field."""
        if value and hasattr(current_app, 'extensions') and 'security_manager' in current_app.extensions:
            security_manager = current_app.extensions['security_manager']
            self._amount = security_manager.encrypt_data(value)
        else:
            self._amount = value
    
    @property
    def terminal_id(self):
        """Decrypt terminal_id field."""
        if hasattr(current_app, 'extensions') and 'security_manager' in current_app.extensions:
            security_manager = current_app.extensions['security_manager']
            if self._terminal_id:
                return security_manager.decrypt_data(self._terminal_id)
        return self._terminal_id
    
    @terminal_id.setter
    def terminal_id(self, value):
        """Encrypt terminal_id field."""
        if value and hasattr(current_app, 'extensions') and 'security_manager' in current_app.extensions:
            security_manager = current_app.extensions['security_manager']
            self._terminal_id = security_manager.encrypt_data(value)
        else:
            self._terminal_id = value
    
    @property
    def merchant_id(self):
        """Decrypt merchant_id field."""
        if hasattr(current_app, 'extensions') and 'security_manager' in current_app.extensions:
            security_manager = current_app.extensions['security_manager']
            if self._merchant_id:
                return security_manager.decrypt_data(self._merchant_id)
        return self._merchant_id
    
    @merchant_id.setter
    def merchant_id(self, value):
        """Encrypt merchant_id field."""
        if value and hasattr(current_app, 'extensions') and 'security_manager' in current_app.extensions:
            security_manager = current_app.extensions['security_manager']
            self._merchant_id = security_manager.encrypt_data(value)
        else:
            self._merchant_id = value
    
    @property
    def raw_message(self):
        """Decrypt raw_message field."""
        if hasattr(current_app, 'extensions') and 'security_manager' in current_app.extensions:
            security_manager = current_app.extensions['security_manager']
            if self._raw_message:
                return security_manager.decrypt_data(self._raw_message)
        return self._raw_message
    
    @raw_message.setter
    def raw_message(self, value):
        """Encrypt raw_message field."""
        if value and hasattr(current_app, 'extensions') and 'security_manager' in current_app.extensions:
            security_manager = current_app.extensions['security_manager']
            self._raw_message = security_manager.encrypt_data(value)
        else:
            self._raw_message = value
    
    def update_access_stats(self):
        """Update access statistics and log the access."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
        audit_logger.info(f"TRANSACTION:ACCESS | ID: {self.id} | MTI: {self.mti} | Count: {self.access_count}")
    
    def calculate_hash(self):
        """Calculate a hash of critical transaction fields for integrity verification."""
        if hasattr(current_app, 'extensions') and 'security_manager' in current_app.extensions:
            security_manager = current_app.extensions['security_manager']
            hash_data = f"{self.id}:{self.mti}:{self._amount}:{self.stan}:{self.rrn}:{self._terminal_id}:{self._merchant_id}"
            self.hash_value = security_manager.hash_data(hash_data)
            return self.hash_value
        return None
    
    def verify_integrity(self):
        """Verify the transaction has not been tampered with."""
        if not self.hash_value:
            return False
            
        if hasattr(current_app, 'extensions') and 'security_manager' in current_app.extensions:
            security_manager = current_app.extensions['security_manager']
            hash_data = f"{self.id}:{self.mti}:{self._amount}:{self.stan}:{self.rrn}:{self._terminal_id}:{self._merchant_id}"
            return security_manager.verify_hash(hash_data, self.hash_value)
        return False
    
    def __repr__(self):
        return f"<Transaction {self.id}>"
    
    def to_dict(self):
        """Convert transaction to dictionary for JSON serialization"""
        # Update access stats when data is accessed
        self.update_access_stats()
        
        return {
            'id': self.id,
            'mti': self.mti,
            'processingCode': self.processing_code,
            'amount': self.amount,
            'transmissionDatetime': self.transmission_datetime,
            'stan': self.stan,
            'rrn': self.rrn,
            'responseCode': self.response_code,
            'terminalId': self.terminal_id,
            'merchantId': self.merchant_id,
            'direction': self.direction,
            'rawMessage': self.raw_message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'access_count': self.access_count
        }


class SystemStatus(db.Model):
    """
    Model for storing system status information
    This is used for caching data from the transaction processor
    """
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20))
    start_time = db.Column(db.DateTime)
    transactions_processed = db.Column(db.BigInteger)
    last_updated = db.Column(db.DateTime)
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, nullable=True)
    access_count = db.Column(db.Integer, default=0)
    
    def __init__(self, **kwargs):
        """Initialize system status with audit logging."""
        super(SystemStatus, self).__init__(**kwargs)
        # Log creation
        audit_logger.info(f"SYSTEM_STATUS:CREATE | ID: {self.id} | Status: {self.status}")
    
    def update_access_stats(self):
        """Update access statistics and log the access."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
        audit_logger.info(f"SYSTEM_STATUS:ACCESS | ID: {self.id} | Status: {self.status} | Count: {self.access_count}")
    
    def __repr__(self):
        return f"<SystemStatus {self.status}>"
    
    def to_dict(self):
        """Convert system status to dictionary for JSON serialization"""
        # Update access stats when data is accessed
        self.update_access_stats()
        
        return {
            'id': self.id,
            'status': self.status,
            'startTime': self.start_time.isoformat() if self.start_time else None,
            'transactionsProcessed': self.transactions_processed,
            'lastUpdated': self.last_updated.isoformat() if self.last_updated else None,
            'access_count': self.access_count
        }


class User(UserMixin, db.Model):
    """
    User model for authentication and access control
    """
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0)
    failed_login_count = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        """Initialize user with password hashing and audit logging."""
        # Extract and hash password if provided
        if 'password' in kwargs:
            self.set_password(kwargs.pop('password'))
            
        # Pass remaining fields to parent constructor
        super(User, self).__init__(**kwargs)
        
        # Log creation
        audit_logger.info(f"USER:CREATE | ID: {self.id} | Username: {self.username}")
    
    def set_password(self, password):
        """Generate password hash and update the password_changed_at timestamp"""
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
        self.failed_login_count = 0  # Reset failed logins when password changes
        audit_logger.info(f"USER:PASSWORD_CHANGE | ID: {self.id} | Username: {self.username}")
    
    def check_password(self, password):
        """Check password against stored hash"""
        result = check_password_hash(self.password_hash, password)
        
        if result:
            # Reset failed login count on successful login
            self.failed_login_count = 0
        else:
            # Increment failed login count
            self.failed_login_count += 1
            self.last_failed_login = datetime.utcnow()
            audit_logger.warning(f"USER:FAILED_LOGIN | ID: {self.id} | Username: {self.username} | Count: {self.failed_login_count}")
        
        return result
    
    def log_login(self):
        """Update login statistics"""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        audit_logger.info(f"USER:LOGIN | ID: {self.id} | Username: {self.username} | Count: {self.login_count}")
    
    def lock_account(self):
        """Lock user account"""
        self.is_active = False
        audit_logger.warning(f"USER:ACCOUNT_LOCKED | ID: {self.id} | Username: {self.username}")
    
    def unlock_account(self):
        """Unlock user account"""
        self.is_active = True
        self.failed_login_count = 0
        audit_logger.info(f"USER:ACCOUNT_UNLOCKED | ID: {self.id} | Username: {self.username}")
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    def to_dict(self):
        """Convert user to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
