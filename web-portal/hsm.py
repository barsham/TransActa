"""
HSM (Hardware Security Module) integration for SillyPostilion.

This module provides functionality to interact with Hardware Security Modules 
for secure cryptographic operations in payment processing environments.

It implements the following key security operations:
1. PIN encryption/decryption
2. Message Authentication Code (MAC) generation/verification
3. Key management (generation, import, export)

The module supports connection to physical HSMs through PKCS#11 interface.
"""

import os
import logging
import base64
import binascii
from typing import Optional, Dict, List, Tuple, Union, Any
from enum import Enum

# PKCS#11 library for HSM interaction
import pkcs11
from pkcs11 import Mechanism, KeyType, ObjectClass, Attribute

# Configure logger
logger = logging.getLogger('hsm')
handler = logging.FileHandler('hsm.log')
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Constants for HSM operations
CLASS_PIN_KEY = 0
CLASS_MAC_KEY = 1
CLASS_ENC_KEY = 2

class HSMKeyType(Enum):
    """Types of keys used in payment processing"""
    PEK = "PIN Encryption Key"            # For PIN block encryption/decryption
    TMK = "Terminal Master Key"          # Master key for terminal communication
    ZMK = "Zone Master Key"              # For secure key exchange between zones
    MAC = "Message Authentication Key"    # For MAC calculation
    BDK = "Base Derivation Key"          # For DUKPT key derivation

class HSMPIN(Enum):
    """PIN block formats"""
    ISO_0 = "ISO-0"  # Format used in ISO 9564-1, ANSI X9.8
    ISO_1 = "ISO-1"  # PIN and account number format
    ISO_3 = "ISO-3"  # Format used in Visa PVV

class HSMError(Exception):
    """Base class for HSM-related exceptions"""
    pass

class HSMConnectionError(HSMError):
    """Raised when connection to the HSM fails"""
    pass

class HSMAuthenticationError(HSMError):
    """Raised when authentication with the HSM fails"""
    pass

class HSMOperationError(HSMError):
    """Raised when a cryptographic operation fails"""
    pass

class HSMManager:
    """Manages connections and operations with Hardware Security Modules"""
    
    def __init__(self, hsm_lib_path: Optional[str] = None, hsm_slot: int = 0):
        """Initialize the HSM Manager
        
        Args:
            hsm_lib_path: Path to the PKCS#11 library for the HSM
            hsm_slot: Slot number for the HSM
        """
        self.hsm_lib_path = hsm_lib_path or os.environ.get('HSM_LIB_PATH')
        self.hsm_slot = hsm_slot
        self.hsm_pin = os.environ.get('HSM_PIN')
        self.session = None
        self.lib = None
        self.slot = None
        self.connected = False
        
        if not self.hsm_lib_path:
            logger.warning("No HSM library path provided. Using software emulation.")
        
    def connect(self) -> bool:
        """Establish connection to the HSM
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if not self.hsm_lib_path:
                logger.warning("Using software emulation for HSM operations")
                self.connected = True
                return True
            
            # Load the PKCS#11 library
            self.lib = pkcs11.lib(self.hsm_lib_path)
            
            # Get the slot and token
            self.slot = self.lib.get_slot(slot_id=self.hsm_slot)
            token = self.slot.get_token()
            
            # Open a session
            self.session = token.open_session(user_pin=self.hsm_pin)
            
            logger.info("Successfully connected to HSM")
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to HSM: {str(e)}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Close connection to the HSM"""
        if self.session:
            try:
                self.session.close()
                logger.info("HSM session closed")
            except Exception as e:
                logger.error(f"Error closing HSM session: {str(e)}")
            finally:
                self.session = None
                self.connected = False
    
    def _ensure_connection(self) -> None:
        """Ensure there's an active connection to the HSM"""
        if not self.connected:
            if not self.connect():
                raise HSMConnectionError("Not connected to HSM")
    
    def generate_key(self, key_type: HSMKeyType, key_length: int = 256) -> Dict[str, Any]:
        """Generate a new key in the HSM
        
        Args:
            key_type: Type of key to generate
            key_length: Length of the key in bits
            
        Returns:
            Dictionary containing key information and handle
        """
        self._ensure_connection()
        
        try:
            if not self.hsm_lib_path:  # Software emulation
                # Generate a random key for software emulation
                import secrets
                key_bytes = secrets.token_bytes(key_length // 8)
                key_id = secrets.token_hex(8)
                key_check_value = self._calculate_check_value(key_bytes)
                
                logger.info(f"Generated software emulated key of type {key_type.name}")
                return {
                    'key_id': key_id,
                    'key_type': key_type,
                    'check_value': key_check_value,
                    '_key_bytes': key_bytes  # For software emulation only
                }
            
            # Real HSM key generation
            key_label = f"{key_type.name}_{os.urandom(4).hex()}"
            
            if key_type in [HSMKeyType.PEK, HSMKeyType.TMK, HSMKeyType.ZMK, HSMKeyType.BDK]:
                key = self.session.generate_key(
                    mechanism=Mechanism.AES_KEY_GEN,
                    label=key_label,
                    id=os.urandom(8),
                    key_type=KeyType.AES,
                    encrypt=True,
                    decrypt=True,
                    wrap=True,
                    unwrap=True,
                    derive=True,
                    token=True
                )
            elif key_type == HSMKeyType.MAC:
                key = self.session.generate_key(
                    mechanism=Mechanism.AES_KEY_GEN,
                    label=key_label,
                    id=os.urandom(8),
                    key_type=KeyType.AES,
                    sign=True,
                    verify=True,
                    token=True
                )
            
            # Get key attributes
            key_id = key[Attribute.ID]
            
            # Calculate check value
            check_value = self._get_key_check_value(key)
            
            logger.info(f"Generated HSM key of type {key_type.name} with ID {binascii.hexlify(key_id).decode()}")
            return {
                'key_id': binascii.hexlify(key_id).decode(),
                'key_type': key_type,
                'check_value': check_value,
                '_key_handle': key  # Store key handle for HSM operations
            }
            
        except Exception as e:
            logger.error(f"Error generating key: {str(e)}")
            raise HSMOperationError(f"Key generation failed: {str(e)}")
    
    def _get_key_check_value(self, key) -> str:
        """Get the key check value (KCV) for a key
        
        Args:
            key: HSM key handle
            
        Returns:
            Key check value as a hexadecimal string
        """
        try:
            # Encrypt a zero block to get check value
            zero_block = bytes([0] * 16)
            encrypted = key.encrypt(zero_block, mechanism=Mechanism.AES_ECB)
            # Return first 3 bytes of the encrypted block
            return binascii.hexlify(encrypted[:3]).decode().upper()
        except Exception as e:
            logger.error(f"Error calculating check value: {str(e)}")
            return "ERROR"
    
    def _calculate_check_value(self, key_bytes: bytes) -> str:
        """Calculate key check value for software emulation
        
        Args:
            key_bytes: Raw key bytes
            
        Returns:
            Key check value as a hexadecimal string
        """
        from Cryptodome.Cipher import AES
        try:
            # Create AES cipher with the key
            cipher = AES.new(key_bytes, AES.MODE_ECB)
            # Encrypt a zero block
            zero_block = bytes([0] * 16)
            encrypted = cipher.encrypt(zero_block)
            # Return first 3 bytes as KCV
            return binascii.hexlify(encrypted[:3]).decode().upper()
        except Exception as e:
            logger.error(f"Error calculating check value: {str(e)}")
            return "ERROR"
    
    def encrypt_pin_block(self, pin: str, pan: str, key_info: Dict[str, Any], 
                         pin_format: HSMPIN = HSMPIN.ISO_0) -> str:
        """Encrypt a PIN using specified format and key
        
        Args:
            pin: PIN to encrypt
            pan: Primary Account Number
            key_info: Key information dictionary
            pin_format: PIN block format
            
        Returns:
            Encrypted PIN block in hexadecimal format
        """
        self._ensure_connection()
        
        try:
            # Format the PIN block
            pin_block = self._format_pin_block(pin, pan, pin_format)
            
            if not self.hsm_lib_path:  # Software emulation
                from Cryptodome.Cipher import AES
                key_bytes = key_info.get('_key_bytes')
                if not key_bytes:
                    raise HSMOperationError("Invalid key for PIN encryption")
                
                # Create AES cipher with the key
                cipher = AES.new(key_bytes, AES.MODE_ECB)
                # Encrypt the PIN block
                encrypted = cipher.encrypt(pin_block)
                return binascii.hexlify(encrypted).decode().upper()
            
            # Real HSM encryption
            key_handle = key_info.get('_key_handle')
            if not key_handle:
                raise HSMOperationError("Invalid key for PIN encryption")
            
            encrypted = key_handle.encrypt(pin_block, mechanism=Mechanism.AES_ECB)
            return binascii.hexlify(encrypted).decode().upper()
            
        except Exception as e:
            logger.error(f"Error encrypting PIN block: {str(e)}")
            raise HSMOperationError(f"PIN encryption failed: {str(e)}")
    
    def decrypt_pin_block(self, encrypted_pin_block: str, pan: str, 
                         key_info: Dict[str, Any], pin_format: HSMPIN = HSMPIN.ISO_0) -> str:
        """Decrypt a PIN block using specified key
        
        Args:
            encrypted_pin_block: Encrypted PIN block in hexadecimal format
            pan: Primary Account Number
            key_info: Key information dictionary
            pin_format: PIN block format
            
        Returns:
            Decrypted PIN
        """
        self._ensure_connection()
        
        try:
            # Convert hex string to bytes
            enc_block_bytes = binascii.unhexlify(encrypted_pin_block)
            
            if not self.hsm_lib_path:  # Software emulation
                from Cryptodome.Cipher import AES
                key_bytes = key_info.get('_key_bytes')
                if not key_bytes:
                    raise HSMOperationError("Invalid key for PIN decryption")
                
                # Create AES cipher with the key
                cipher = AES.new(key_bytes, AES.MODE_ECB)
                # Decrypt the PIN block
                decrypted = cipher.decrypt(enc_block_bytes)
            else:
                # Real HSM decryption
                key_handle = key_info.get('_key_handle')
                if not key_handle:
                    raise HSMOperationError("Invalid key for PIN decryption")
                
                decrypted = key_handle.decrypt(enc_block_bytes, mechanism=Mechanism.AES_ECB)
            
            # Extract PIN from the decrypted PIN block
            pin = self._extract_pin_from_block(decrypted, pan, pin_format)
            return pin
            
        except Exception as e:
            logger.error(f"Error decrypting PIN block: {str(e)}")
            raise HSMOperationError(f"PIN decryption failed: {str(e)}")
    
    def _format_pin_block(self, pin: str, pan: str, pin_format: HSMPIN) -> bytes:
        """Format a PIN block according to specified format
        
        Args:
            pin: PIN to format
            pan: Primary Account Number
            pin_format: PIN block format
            
        Returns:
            Formatted PIN block as bytes
        """
        if pin_format == HSMPIN.ISO_0:
            # ISO-0 format
            pin_len = len(pin)
            block = bytearray(16)
            
            # PIN format: '0' + PIN length (1 digit) + PIN + Padding 'F'
            block[0] = 0  # Format code
            block[1] = pin_len  # PIN length
            
            # Add PIN digits
            for i in range(pin_len):
                if i < 14:  # Maximum 14 PIN digits
                    block[2 + i // 2] |= (int(pin[i]) << (4 if i % 2 else 0))
            
            # Fill the rest with 'F'
            for i in range(2 + (pin_len + 1) // 2, 8):
                block[i] = 0xFF
                
            return bytes(block)
            
        elif pin_format == HSMPIN.ISO_1:
            # ISO-1 format (combines PIN with PAN)
            pin_len = len(pin)
            block1 = bytearray(8)
            block2 = bytearray(8)
            
            # PIN format in block1: '1' + PIN length (1 digit) + PIN + Padding 'F'
            block1[0] = 0x10 | pin_len  # Format code + PIN length
            
            # Add PIN digits to block1
            for i in range(pin_len):
                if i < 14:  # Maximum 14 PIN digits
                    idx = (i + 2) // 2
                    shift = 4 if (i + 2) % 2 else 0
                    block1[idx] |= (int(pin[i]) << shift)
            
            # Fill the rest with 'F'
            for i in range(1 + (pin_len + 1) // 2, 8):
                block1[i] = 0xFF
            
            # Format PAN for block2 (last 12 digits excluding check digit)
            pan_digits = pan[-13:-1]  # Exclude check digit
            for i in range(min(12, len(pan_digits))):
                idx = i // 2
                shift = 4 if i % 2 else 0
                block2[idx] |= (int(pan_digits[i]) << shift)
            
            # XOR the blocks to create final PIN block
            result = bytearray(8)
            for i in range(8):
                result[i] = block1[i] ^ block2[i]
                
            return bytes(result)
            
        elif pin_format == HSMPIN.ISO_3:
            # ISO-3 format (for Visa PVV)
            # Simplified implementation
            pin_len = len(pin)
            block = bytearray(8)
            
            # PIN format: '3' + PIN length (1 digit) + PIN + Padding 'F'
            block[0] = 0x30 | pin_len  # Format code + PIN length
            
            # Add PIN digits
            for i in range(pin_len):
                if i < 14:  # Maximum 14 PIN digits
                    idx = (i + 2) // 2
                    shift = 4 if (i + 2) % 2 else 0
                    block[idx] |= (int(pin[i]) << shift)
            
            # Fill the rest with 'F'
            for i in range(1 + (pin_len + 1) // 2, 8):
                block[i] = 0xFF
                
            return bytes(block)
        
        else:
            raise ValueError(f"Unsupported PIN format: {pin_format}")
    
    def _extract_pin_from_block(self, pin_block: bytes, pan: str, pin_format: HSMPIN) -> str:
        """Extract PIN from a decrypted PIN block
        
        Args:
            pin_block: Decrypted PIN block
            pan: Primary Account Number
            pin_format: PIN block format
            
        Returns:
            Extracted PIN
        """
        if pin_format == HSMPIN.ISO_0:
            # ISO-0 format
            if pin_block[0] != 0:
                raise ValueError("Invalid PIN block format")
                
            pin_len = pin_block[1] & 0x0F
            if pin_len < 4 or pin_len > 12:
                raise ValueError(f"Invalid PIN length: {pin_len}")
                
            pin = ''
            for i in range(pin_len):
                byte_idx = 2 + i // 2
                if i % 2 == 0:
                    pin_digit = (pin_block[byte_idx] >> 4) & 0x0F
                else:
                    pin_digit = pin_block[byte_idx] & 0x0F
                pin += str(pin_digit)
                
            return pin
            
        elif pin_format == HSMPIN.ISO_1:
            # ISO-1 format
            # Create PAN block for XOR
            pan_block = bytearray(8)
            pan_digits = pan[-13:-1]  # Exclude check digit
            
            for i in range(min(12, len(pan_digits))):
                idx = i // 2
                shift = 4 if i % 2 else 0
                pan_block[idx] |= (int(pan_digits[i]) << shift)
            
            # XOR with PAN block to get original PIN block
            pin_data = bytearray(8)
            for i in range(8):
                pin_data[i] = pin_block[i] ^ pan_block[i]
            
            # Extract PIN length and PIN
            format_and_len = pin_data[0]
            if (format_and_len & 0xF0) != 0x10:
                raise ValueError("Invalid PIN block format")
                
            pin_len = format_and_len & 0x0F
            if pin_len < 4 or pin_len > 12:
                raise ValueError(f"Invalid PIN length: {pin_len}")
                
            pin = ''
            for i in range(pin_len):
                byte_idx = 1 + i // 2
                if i % 2 == 0:
                    pin_digit = (pin_data[byte_idx] >> 4) & 0x0F
                else:
                    pin_digit = pin_data[byte_idx] & 0x0F
                pin += str(pin_digit)
                
            return pin
            
        elif pin_format == HSMPIN.ISO_3:
            # ISO-3 format
            format_and_len = pin_block[0]
            if (format_and_len & 0xF0) != 0x30:
                raise ValueError("Invalid PIN block format")
                
            pin_len = format_and_len & 0x0F
            if pin_len < 4 or pin_len > 12:
                raise ValueError(f"Invalid PIN length: {pin_len}")
                
            pin = ''
            for i in range(pin_len):
                byte_idx = 1 + i // 2
                if i % 2 == 0:
                    pin_digit = (pin_block[byte_idx] >> 4) & 0x0F
                else:
                    pin_digit = pin_block[byte_idx] & 0x0F
                pin += str(pin_digit)
                
            return pin
        
        else:
            raise ValueError(f"Unsupported PIN format: {pin_format}")
    
    def generate_mac(self, message: bytes, key_info: Dict[str, Any]) -> str:
        """Generate a Message Authentication Code (MAC)
        
        Args:
            message: Message to generate MAC for
            key_info: Key information dictionary
            
        Returns:
            MAC value in hexadecimal format
        """
        self._ensure_connection()
        
        try:
            if not self.hsm_lib_path:  # Software emulation
                from Cryptodome.Cipher import AES
                from Cryptodome.Hash import CMAC
                
                key_bytes = key_info.get('_key_bytes')
                if not key_bytes:
                    raise HSMOperationError("Invalid key for MAC generation")
                
                # Use CMAC algorithm
                cobj = CMAC.new(key_bytes, ciphermod=AES)
                cobj.update(message)
                return cobj.hexdigest().upper()
            
            # Real HSM MAC generation
            key_handle = key_info.get('_key_handle')
            if not key_handle:
                raise HSMOperationError("Invalid key for MAC generation")
            
            mac = key_handle.sign(message, mechanism=Mechanism.AES_CMAC)
            return binascii.hexlify(mac).decode().upper()
            
        except Exception as e:
            logger.error(f"Error generating MAC: {str(e)}")
            raise HSMOperationError(f"MAC generation failed: {str(e)}")
    
    def verify_mac(self, message: bytes, mac: str, key_info: Dict[str, Any]) -> bool:
        """Verify a Message Authentication Code (MAC)
        
        Args:
            message: Original message
            mac: MAC value in hexadecimal format
            key_info: Key information dictionary
            
        Returns:
            True if MAC is valid, False otherwise
        """
        self._ensure_connection()
        
        try:
            mac_bytes = binascii.unhexlify(mac)
            
            if not self.hsm_lib_path:  # Software emulation
                from Cryptodome.Cipher import AES
                from Cryptodome.Hash import CMAC
                
                key_bytes = key_info.get('_key_bytes')
                if not key_bytes:
                    raise HSMOperationError("Invalid key for MAC verification")
                
                # Use CMAC algorithm
                cobj = CMAC.new(key_bytes, ciphermod=AES)
                cobj.update(message)
                calculated_mac = cobj.digest()
                return calculated_mac == mac_bytes
            
            # Real HSM MAC verification
            key_handle = key_info.get('_key_handle')
            if not key_handle:
                raise HSMOperationError("Invalid key for MAC verification")
            
            try:
                key_handle.verify(message, mac_bytes, mechanism=Mechanism.AES_CMAC)
                return True
            except pkcs11.MechanismError:
                return False
            
        except Exception as e:
            logger.error(f"Error verifying MAC: {str(e)}")
            raise HSMOperationError(f"MAC verification failed: {str(e)}")
    
    def import_key(self, encrypted_key: str, kek_info: Dict[str, Any], 
                   key_type: HSMKeyType) -> Dict[str, Any]:
        """Import an encrypted key into the HSM
        
        Args:
            encrypted_key: Encrypted key in hexadecimal format
            kek_info: Key encryption key information
            key_type: Type of key being imported
            
        Returns:
            Key information dictionary
        """
        self._ensure_connection()
        
        try:
            # Convert hex string to bytes
            enc_key_bytes = binascii.unhexlify(encrypted_key)
            
            if not self.hsm_lib_path:  # Software emulation
                from Cryptodome.Cipher import AES
                kek_bytes = kek_info.get('_key_bytes')
                if not kek_bytes:
                    raise HSMOperationError("Invalid key encryption key")
                
                # Create AES cipher with the KEK
                cipher = AES.new(kek_bytes, AES.MODE_ECB)
                # Decrypt the key
                key_bytes = cipher.decrypt(enc_key_bytes)
                key_id = os.urandom(8).hex()
                key_check_value = self._calculate_check_value(key_bytes)
                
                logger.info(f"Imported software emulated key of type {key_type.name}")
                return {
                    'key_id': key_id,
                    'key_type': key_type,
                    'check_value': key_check_value,
                    '_key_bytes': key_bytes  # For software emulation only
                }
            
            # Real HSM key import
            kek_handle = kek_info.get('_key_handle')
            if not kek_handle:
                raise HSMOperationError("Invalid key encryption key")
            
            key_label = f"{key_type.name}_{os.urandom(4).hex()}"
            key_id = os.urandom(8)
            
            if key_type in [HSMKeyType.PEK, HSMKeyType.TMK, HSMKeyType.ZMK, HSMKeyType.BDK]:
                key = self.session.unwrap_key(
                    kek_handle,
                    key_type=KeyType.AES,
                    mechanism=Mechanism.AES_ECB,
                    wrapped_key=enc_key_bytes,
                    label=key_label,
                    id=key_id,
                    encrypt=True,
                    decrypt=True,
                    wrap=True,
                    unwrap=True,
                    derive=True,
                    token=True
                )
            elif key_type == HSMKeyType.MAC:
                key = self.session.unwrap_key(
                    kek_handle,
                    key_type=KeyType.AES,
                    mechanism=Mechanism.AES_ECB,
                    wrapped_key=enc_key_bytes,
                    label=key_label,
                    id=key_id,
                    sign=True,
                    verify=True,
                    token=True
                )
            
            # Get key check value
            check_value = self._get_key_check_value(key)
            
            logger.info(f"Imported HSM key of type {key_type.name} with ID {binascii.hexlify(key_id).decode()}")
            return {
                'key_id': binascii.hexlify(key_id).decode(),
                'key_type': key_type,
                'check_value': check_value,
                '_key_handle': key  # Store key handle for HSM operations
            }
            
        except Exception as e:
            logger.error(f"Error importing key: {str(e)}")
            raise HSMOperationError(f"Key import failed: {str(e)}")
    
    def export_key(self, key_info: Dict[str, Any], kek_info: Dict[str, Any]) -> str:
        """Export a key encrypted under a key encryption key
        
        Args:
            key_info: Key information dictionary for the key to export
            kek_info: Key encryption key information
            
        Returns:
            Encrypted key in hexadecimal format
        """
        self._ensure_connection()
        
        try:
            if not self.hsm_lib_path:  # Software emulation
                from Cryptodome.Cipher import AES
                key_bytes = key_info.get('_key_bytes')
                kek_bytes = kek_info.get('_key_bytes')
                
                if not key_bytes or not kek_bytes:
                    raise HSMOperationError("Invalid keys for export operation")
                
                # Create AES cipher with the KEK
                cipher = AES.new(kek_bytes, AES.MODE_ECB)
                # Encrypt the key
                encrypted = cipher.encrypt(key_bytes)
                return binascii.hexlify(encrypted).decode().upper()
            
            # Real HSM key export
            key_handle = key_info.get('_key_handle')
            kek_handle = kek_info.get('_key_handle')
            
            if not key_handle or not kek_handle:
                raise HSMOperationError("Invalid keys for export operation")
            
            wrapped_key = self.session.wrap_key(
                kek_handle,
                key_handle,
                mechanism=Mechanism.AES_ECB
            )
            
            return binascii.hexlify(wrapped_key).decode().upper()
            
        except Exception as e:
            logger.error(f"Error exporting key: {str(e)}")
            raise HSMOperationError(f"Key export failed: {str(e)}")


# Create an instance of the HSM Manager
hsm_manager = HSMManager()


def get_hsm_manager() -> HSMManager:
    """Return the HSM manager instance"""
    return hsm_manager