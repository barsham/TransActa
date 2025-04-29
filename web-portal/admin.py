"""
Admin Module for SillyPostilion

This module provides administrative functionality for managing:
1. Connection endpoints
2. HSM key management
3. User permissions
4. System settings
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum

from flask import current_app
from hsm import HSMKeyType, get_hsm_manager

# Configure logger
logger = logging.getLogger('admin')
handler = logging.FileHandler('admin.log')
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Constants
CONFIG_DIR = 'config'
ENDPOINTS_FILE = os.path.join(CONFIG_DIR, 'endpoints.json')
HSM_KEYS_FILE = os.path.join(CONFIG_DIR, 'hsm_keys.json')
SETTINGS_FILE = os.path.join(CONFIG_DIR, 'settings.json')

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

class EndpointType(str, Enum):
    """Types of connection endpoints"""
    ACQUIRER = "acquirer"        # Connection to an acquirer
    ISSUER = "issuer"            # Connection to an issuer
    NETWORK = "network"          # Connection to a payment network
    SIMULATOR = "simulator"      # Connection to a simulator
    API = "api"                  # API endpoint

class EndpointProtocol(str, Enum):
    """Communication protocols for endpoints"""
    TCP = "tcp"                # Raw TCP/IP
    HTTP = "http"              # HTTP
    HTTPS = "https"            # HTTPS (Secure HTTP)
    WEBSOCKET = "websocket"    # WebSocket

class AuthMethod(str, Enum):
    """Authentication methods for endpoints"""
    NONE = "none"                  # No authentication
    BASIC = "basic"                # Basic authentication
    CERTIFICATE = "certificate"    # Certificate-based authentication
    OAUTH = "oauth"                # OAuth token
    HMAC = "hmac"                  # HMAC-based authentication

@dataclass
class Endpoint:
    """Connection endpoint configuration"""
    id: str
    name: str
    description: str
    endpoint_type: EndpointType
    protocol: EndpointProtocol
    host: str
    port: int
    path: str = ""
    auth_method: AuthMethod = AuthMethod.NONE
    auth_credentials: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_attempts: int = 3
    ssl_verify: bool = True
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert endpoint to dictionary"""
        return {
            key: (value.value if isinstance(value, Enum) else value)
            for key, value in asdict(self).items()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Endpoint':
        """Create endpoint from dictionary"""
        # Convert string enum values to enum types
        if 'endpoint_type' in data:
            data['endpoint_type'] = EndpointType(data['endpoint_type'])
        if 'protocol' in data:
            data['protocol'] = EndpointProtocol(data['protocol'])
        if 'auth_method' in data:
            data['auth_method'] = AuthMethod(data['auth_method'])
        
        # Filter out any extra keys not in the dataclass
        valid_fields = [field.name for field in cls.__dataclass_fields__.values()]
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)

@dataclass
class HSMKeyEntry:
    """HSM key entry for the key registry"""
    id: str
    name: str
    description: str
    key_type: str  # HSMKeyType as string
    check_value: str
    created_at: str
    rotation_date: Optional[str] = None
    expired: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert HSM key entry to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HSMKeyEntry':
        """Create HSM key entry from dictionary"""
        # Filter out any extra keys not in the dataclass
        valid_fields = [field.name for field in cls.__dataclass_fields__.values()]
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)

@dataclass
class Settings:
    """System settings"""
    transaction_processor_url: str = "http://localhost:8000"
    log_level: str = "INFO"
    session_timeout: int = 30  # minutes
    max_failed_logins: int = 5
    password_expiry_days: int = 90
    audit_retention_days: int = 365
    enable_pin_verification: bool = True
    enable_mac_verification: bool = True
    offline_mode: bool = False
    maintenance_mode: bool = False
    updated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        """Create settings from dictionary"""
        # Filter out any extra keys not in the dataclass
        valid_fields = [field.name for field in cls.__dataclass_fields__.values()]
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)

class AdminModule:
    """Main class for administrative operations"""
    
    def __init__(self):
        """Initialize the admin module"""
        self.endpoints = self._load_endpoints()
        self.hsm_keys = self._load_hsm_keys()
        self.settings = self._load_settings()
    
    def _load_endpoints(self) -> List[Endpoint]:
        """Load endpoints from configuration file"""
        try:
            if os.path.exists(ENDPOINTS_FILE):
                with open(ENDPOINTS_FILE, 'r') as f:
                    data = json.load(f)
                    return [Endpoint.from_dict(item) for item in data]
            return []
        except Exception as e:
            logger.error(f"Error loading endpoints: {str(e)}")
            return []
    
    def _save_endpoints(self) -> bool:
        """Save endpoints to configuration file"""
        try:
            data = [endpoint.to_dict() for endpoint in self.endpoints]
            os.makedirs(os.path.dirname(ENDPOINTS_FILE), exist_ok=True)
            with open(ENDPOINTS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving endpoints: {str(e)}")
            return False
    
    def _load_hsm_keys(self) -> List[HSMKeyEntry]:
        """Load HSM keys from configuration file"""
        try:
            if os.path.exists(HSM_KEYS_FILE):
                with open(HSM_KEYS_FILE, 'r') as f:
                    data = json.load(f)
                    return [HSMKeyEntry.from_dict(item) for item in data]
            return []
        except Exception as e:
            logger.error(f"Error loading HSM keys: {str(e)}")
            return []
    
    def _save_hsm_keys(self) -> bool:
        """Save HSM keys to configuration file"""
        try:
            data = [key.to_dict() for key in self.hsm_keys]
            os.makedirs(os.path.dirname(HSM_KEYS_FILE), exist_ok=True)
            with open(HSM_KEYS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving HSM keys: {str(e)}")
            return False
    
    def _load_settings(self) -> Settings:
        """Load settings from configuration file"""
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                    return Settings.from_dict(data)
            return Settings()
        except Exception as e:
            logger.error(f"Error loading settings: {str(e)}")
            return Settings()
    
    def _save_settings(self) -> bool:
        """Save settings to configuration file"""
        try:
            data = self.settings.to_dict()
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            return False
    
    def get_endpoints(self, endpoint_type: Optional[EndpointType] = None) -> List[Endpoint]:
        """Get all endpoints or filter by type"""
        if endpoint_type is None:
            return self.endpoints
        
        return [e for e in self.endpoints if e.endpoint_type == endpoint_type]
    
    def get_endpoint(self, endpoint_id: str) -> Optional[Endpoint]:
        """Get endpoint by ID"""
        for endpoint in self.endpoints:
            if endpoint.id == endpoint_id:
                return endpoint
        return None
    
    def add_endpoint(self, endpoint: Endpoint) -> bool:
        """Add a new endpoint"""
        # Check if endpoint with same ID already exists
        if any(e.id == endpoint.id for e in self.endpoints):
            logger.error(f"Endpoint with ID {endpoint.id} already exists")
            return False
        
        # Add endpoint
        endpoint.created_at = datetime.datetime.now().isoformat()
        endpoint.updated_at = endpoint.created_at
        self.endpoints.append(endpoint)
        
        # Save endpoints
        result = self._save_endpoints()
        if result:
            logger.info(f"Added endpoint: {endpoint.name} ({endpoint.id})")
        
        return result
    
    def update_endpoint(self, endpoint_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing endpoint"""
        for i, endpoint in enumerate(self.endpoints):
            if endpoint.id == endpoint_id:
                # Update fields
                for key, value in updates.items():
                    if hasattr(endpoint, key):
                        # Handle enum fields
                        if key == 'endpoint_type' and isinstance(value, str):
                            setattr(endpoint, key, EndpointType(value))
                        elif key == 'protocol' and isinstance(value, str):
                            setattr(endpoint, key, EndpointProtocol(value))
                        elif key == 'auth_method' and isinstance(value, str):
                            setattr(endpoint, key, AuthMethod(value))
                        else:
                            setattr(endpoint, key, value)
                
                # Update timestamp
                endpoint.updated_at = datetime.datetime.now().isoformat()
                self.endpoints[i] = endpoint
                
                # Save endpoints
                result = self._save_endpoints()
                if result:
                    logger.info(f"Updated endpoint: {endpoint.name} ({endpoint.id})")
                
                return result
        
        logger.error(f"Endpoint with ID {endpoint_id} not found")
        return False
    
    def delete_endpoint(self, endpoint_id: str) -> bool:
        """Delete an endpoint"""
        for i, endpoint in enumerate(self.endpoints):
            if endpoint.id == endpoint_id:
                # Remove endpoint
                deleted = self.endpoints.pop(i)
                
                # Save endpoints
                result = self._save_endpoints()
                if result:
                    logger.info(f"Deleted endpoint: {deleted.name} ({deleted.id})")
                
                return result
        
        logger.error(f"Endpoint with ID {endpoint_id} not found")
        return False
    
    def generate_hsm_key(self, name: str, description: str, key_type: HSMKeyType) -> Optional[HSMKeyEntry]:
        """Generate a new HSM key"""
        try:
            # Get HSM manager
            hsm = get_hsm_manager()
            
            # Generate key
            key_info = hsm.generate_key(key_type)
            
            # Create key entry
            now = datetime.datetime.now().isoformat()
            key_entry = HSMKeyEntry(
                id=key_info['key_id'],
                name=name,
                description=description,
                key_type=key_type.name,
                check_value=key_info['check_value'],
                created_at=now
            )
            
            # Add to key registry
            self.hsm_keys.append(key_entry)
            
            # Save key registry
            if self._save_hsm_keys():
                logger.info(f"Generated HSM key: {name} ({key_entry.id})")
                return key_entry
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating HSM key: {str(e)}")
            return None
    
    def import_hsm_key(self, name: str, description: str, key_type: HSMKeyType, 
                        encrypted_key: str, kek_id: str) -> Optional[HSMKeyEntry]:
        """Import an encrypted HSM key"""
        try:
            # Get HSM manager
            hsm = get_hsm_manager()
            
            # Find KEK (Key Encryption Key)
            kek_info = None
            for key in self.hsm_keys:
                if key.id == kek_id:
                    # In a real implementation, we would retrieve the actual key handle
                    # from a secure storage or the HSM itself
                    break
            
            if not kek_info:
                logger.error(f"KEK with ID {kek_id} not found")
                return None
            
            # Import key (this is simplified, in real implementation we would have a secure way
            # to pass the actual KEK handle)
            key_info = hsm.import_key(encrypted_key, {'key_id': kek_id}, key_type)
            
            # Create key entry
            now = datetime.datetime.now().isoformat()
            key_entry = HSMKeyEntry(
                id=key_info['key_id'],
                name=name,
                description=description,
                key_type=key_type.name,
                check_value=key_info['check_value'],
                created_at=now
            )
            
            # Add to key registry
            self.hsm_keys.append(key_entry)
            
            # Save key registry
            if self._save_hsm_keys():
                logger.info(f"Imported HSM key: {name} ({key_entry.id})")
                return key_entry
            
            return None
            
        except Exception as e:
            logger.error(f"Error importing HSM key: {str(e)}")
            return None
    
    def rotate_hsm_key(self, key_id: str) -> Optional[HSMKeyEntry]:
        """Rotate an HSM key (generate new key and mark old as expired)"""
        # Find existing key
        old_key = None
        for key in self.hsm_keys:
            if key.id == key_id:
                old_key = key
                break
        
        if not old_key:
            logger.error(f"Key with ID {key_id} not found")
            return None
        
        # Generate new key with same properties
        try:
            # Get HSM manager
            hsm = get_hsm_manager()
            
            # Generate key
            key_type = HSMKeyType[old_key.key_type]
            key_info = hsm.generate_key(key_type)
            
            # Create key entry
            now = datetime.datetime.now().isoformat()
            key_entry = HSMKeyEntry(
                id=key_info['key_id'],
                name=f"{old_key.name} (rotated)",
                description=f"Rotated from {old_key.id}: {old_key.description}",
                key_type=old_key.key_type,
                check_value=key_info['check_value'],
                created_at=now
            )
            
            # Mark old key as expired
            for i, key in enumerate(self.hsm_keys):
                if key.id == key_id:
                    key.expired = True
                    key.rotation_date = now
                    self.hsm_keys[i] = key
                    break
            
            # Add new key to registry
            self.hsm_keys.append(key_entry)
            
            # Save key registry
            if self._save_hsm_keys():
                logger.info(f"Rotated HSM key: {old_key.id} -> {key_entry.id}")
                return key_entry
            
            return None
            
        except Exception as e:
            logger.error(f"Error rotating HSM key: {str(e)}")
            return None
    
    def get_hsm_keys(self, include_expired: bool = False) -> List[HSMKeyEntry]:
        """Get all HSM keys, optionally including expired ones"""
        if include_expired:
            return self.hsm_keys
        
        return [key for key in self.hsm_keys if not key.expired]
    
    def get_hsm_key(self, key_id: str) -> Optional[HSMKeyEntry]:
        """Get HSM key by ID"""
        for key in self.hsm_keys:
            if key.id == key_id:
                return key
        return None
    
    def update_settings(self, updates: Dict[str, Any]) -> bool:
        """Update system settings"""
        for key, value in updates.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        
        # Update timestamp
        self.settings.updated_at = datetime.datetime.now().isoformat()
        
        # Save settings
        result = self._save_settings()
        if result:
            logger.info(f"Updated settings: {', '.join(updates.keys())}")
        
        return result
    
    def get_settings(self) -> Settings:
        """Get current system settings"""
        return self.settings

# Create an instance of the admin module
admin_module = AdminModule()

def get_admin_module() -> AdminModule:
    """Return the admin module instance"""
    return admin_module
