"""
Security Manager - Enhanced security for Face Recognition System
"""
import os
import hashlib
import secrets
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import stat
from .error_handler import get_error_handler, handle_errors

class SecurityManager:
    """Professional security management"""
    
    def __init__(self, key_file: str = ".security_key"):
        self.key_file = key_file
        self.error_handler = get_error_handler()
        self.cipher_suite = None
        
        # Security settings
        self.max_failed_attempts = 5
        self.lockout_duration = 300  # 5 minutes
        self.failed_attempts = {}
        
        # Initialize encryption
        self._initialize_encryption()
        
        print("🔒 SecurityManager initialized")
    
    def _initialize_encryption(self):
        """Initialize encryption system"""
        try:
            if os.path.exists(self.key_file):
                # Load existing key
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                # Generate new key
                key = Fernet.generate_key()
                
                # Save key with restricted permissions
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                
                # Set file permissions (owner read/write only)
                os.chmod(self.key_file, stat.S_IRUSR | stat.S_IWUSR)
                
                print("🔑 New encryption key generated")
            
            self.cipher_suite = Fernet(key)
            
        except Exception as e:
            self.error_handler.log_error(e, "Encryption initialization")
    
    @handle_errors("File Encryption")
    def encrypt_file(self, filepath: str, data: Dict[str, Any]) -> bool:
        """Encrypt and save sensitive data"""
        try:
            if not self.cipher_suite:
                return False
            
            # Convert to JSON and encrypt
            json_data = json.dumps(data, default=str).encode()
            encrypted_data = self.cipher_suite.encrypt(json_data)
            
            # Save encrypted data
            with open(filepath, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)
            
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, f"File encryption: {filepath}")
            return False
    
    @handle_errors("File Decryption")
    def decrypt_file(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Decrypt and load sensitive data"""
        try:
            if not self.cipher_suite or not os.path.exists(filepath):
                return None
            
            # Load and decrypt data
            with open(filepath, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            
            # Parse JSON
            data = json.loads(decrypted_data.decode())
            
            return data
            
        except Exception as e:
            self.error_handler.log_error(e, f"File decryption: {filepath}")
            return None
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # Use PBKDF2 for password hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = kdf.derive(password.encode())
        
        # Return base64 encoded hash and salt
        return base64.b64encode(key).decode(), base64.b64encode(salt).decode()
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            salt_bytes = base64.b64decode(salt.encode())
            expected_hash, _ = self.hash_password(password, salt_bytes)
            
            return secrets.compare_digest(expected_hash, hashed_password)
            
        except Exception as e:
            self.error_handler.log_error(e, "Password verification")
            return False
    
    def check_access_attempt(self, identifier: str) -> bool:
        """Check if access attempt is allowed (rate limiting)"""
        current_time = datetime.now()
        
        if identifier in self.failed_attempts:
            attempts_data = self.failed_attempts[identifier]
            
            # Check if lockout period has expired
            if current_time - attempts_data['last_attempt'] > timedelta(seconds=self.lockout_duration):
                # Reset failed attempts
                del self.failed_attempts[identifier]
                return True
            
            # Check if max attempts exceeded
            if attempts_data['count'] >= self.max_failed_attempts:
                remaining_time = self.lockout_duration - (current_time - attempts_data['last_attempt']).total_seconds()
                print(f"🚫 Access blocked for {identifier}. Try again in {remaining_time:.0f} seconds")
                return False
        
        return True
    
    def record_failed_attempt(self, identifier: str):
        """Record failed access attempt"""
        current_time = datetime.now()
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = {'count': 0, 'last_attempt': current_time}
        
        self.failed_attempts[identifier]['count'] += 1
        self.failed_attempts[identifier]['last_attempt'] = current_time
        
        print(f"⚠️  Failed attempt recorded for {identifier} ({self.failed_attempts[identifier]['count']}/{self.max_failed_attempts})")
    
    def record_successful_attempt(self, identifier: str):
        """Record successful access attempt"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
    
    def validate_file_permissions(self, filepath: str) -> bool:
        """Validate file has secure permissions"""
        try:
            if not os.path.exists(filepath):
                return False
            
            file_stat = os.stat(filepath)
            file_mode = stat.filemode(file_stat.st_mode)
            
            # Check if file is readable by others
            if file_stat.st_mode & (stat.S_IRGRP | stat.S_IROTH):
                print(f"⚠️  Security warning: {filepath} is readable by others")
                return False
            
            # Check if file is writable by others
            if file_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
                print(f"⚠️  Security warning: {filepath} is writable by others")
                return False
            
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, f"File permission validation: {filepath}")
            return False
    
    def secure_file_permissions(self, filepath: str) -> bool:
        """Set secure file permissions"""
        try:
            if not os.path.exists(filepath):
                return False
            
            # Set owner read/write only
            os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)
            
            print(f"🔒 Secured permissions for {filepath}")
            return True
            
        except Exception as e:
            self.error_handler.log_error(e, f"File permission securing: {filepath}")
            return False
    
    def audit_sensitive_files(self, file_patterns: List[str]) -> Dict[str, bool]:
        """Audit sensitive files for security"""
        import glob
        
        audit_results = {}
        
        for pattern in file_patterns:
            files = glob.glob(pattern)
            
            for filepath in files:
                is_secure = self.validate_file_permissions(filepath)
                audit_results[filepath] = is_secure
                
                if not is_secure:
                    print(f"🚨 Security issue: {filepath}")
        
        return audit_results
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get security status report"""
        return {
            'encryption_enabled': self.cipher_suite is not None,
            'failed_attempts': len(self.failed_attempts),
            'lockout_duration': self.lockout_duration,
            'max_failed_attempts': self.max_failed_attempts,
            'active_lockouts': [
                {
                    'identifier': identifier,
                    'attempts': data['count'],
                    'last_attempt': data['last_attempt'].isoformat()
                }
                for identifier, data in self.failed_attempts.items()
            ]
        }

# Global security manager instance
_security_manager = None

def get_security_manager() -> SecurityManager:
    """Get global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager