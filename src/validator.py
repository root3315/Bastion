#!/usr/bin/env python3
"""
Validator Module

Provides input validation, sanitization, and security checks.
"""

import os
import re
import socket
import string
from pathlib import Path
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, Union
from urllib.parse import urlparse


class Validator:
    """
    Input validator for Bastion.
    
    Provides methods for validating and sanitizing various input types.
    
    Attributes:
        strict: Enable strict validation mode
    """
    
    # Common dangerous patterns
    DANGEROUS_PATTERNS: List[Pattern] = [
        re.compile(r"(\.\./|\.\.\\)"),  # Path traversal
        re.compile(r"[;&|`$()]"),  # Shell injection
        re.compile(r"<script[^>]*>", re.IGNORECASE),  # XSS
        re.compile(r"(\%27)|(\')|(\-\-)|(\%23)|(#)", re.IGNORECASE),  # SQL injection
    ]
    
    # Safe filename characters
    SAFE_FILENAME_PATTERN: Pattern = re.compile(r"^[a-zA-Z0-9_\-. ]+$")
    
    # Email pattern
    EMAIL_PATTERN: Pattern = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    
    # IPv4 pattern
    IPV4_PATTERN: Pattern = re.compile(
        r"^(\d{1,3}\.){3}\d{1,3}$"
    )
    
    # IPv6 pattern (simplified)
    IPV6_PATTERN: Pattern = re.compile(r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$")
    
    def __init__(self, strict: bool = False):
        """
        Initialize validator.
        
        Args:
            strict: Enable strict validation mode
        """
        self.strict = strict
    
    def validate_string(
        self,
        value: str,
        min_length: int = 0,
        max_length: int = 10000,
        allowed_chars: Optional[str] = None,
        block_patterns: Optional[List[Pattern]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a string value.
        
        Args:
            value: String to validate
            min_length: Minimum length
            max_length: Maximum length
            allowed_chars: String of allowed characters
            block_patterns: Additional patterns to block
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(value, str):
            return False, "Value must be a string"
        
        if len(value) < min_length:
            return False, f"String too short (min {min_length})"
        
        if len(value) > max_length:
            return False, f"String too long (max {max_length})"
        
        if allowed_chars is not None:
            allowed_set = set(allowed_chars)
            if not all(c in allowed_set for c in value):
                return False, "String contains invalid characters"
        
        patterns = self.DANGEROUS_PATTERNS + (block_patterns or [])
        for pattern in patterns:
            if pattern.search(value):
                return False, "String contains dangerous pattern"
        
        return True, None
    
    def sanitize_string(
        self,
        value: str,
        remove_chars: Optional[str] = None,
        allowed_chars: Optional[str] = None,
    ) -> str:
        """
        Sanitize a string by removing dangerous characters.
        
        Args:
            value: String to sanitize
            remove_chars: Characters to remove
            allowed_chars: Only keep these characters
            
        Returns:
            Sanitized string
        """
        if remove_chars:
            for char in remove_chars:
                value = value.replace(char, "")
        
        if allowed_chars:
            allowed_set = set(allowed_chars)
            value = "".join(c for c in value if c in allowed_set)
        
        # Remove dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            value = pattern.sub("", value)
        
        return value
    
    def validate_path(
        self,
        path: Union[str, Path],
        must_exist: bool = False,
        base_dir: Optional[Union[str, Path]] = None,
        allow_symlinks: bool = False,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a file path.
        
        Args:
            path: Path to validate
            must_exist: Path must exist
            base_dir: Restrict to this base directory
            allow_symlinks: Allow symbolic links
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        path_obj = Path(path)
        
        # Check for path traversal
        path_str = str(path_obj)
        if ".." in path_str:
            return False, "Path traversal not allowed"
        
        # Resolve to absolute path
        try:
            if must_exist:
                if not path_obj.exists():
                    return False, "Path does not exist"
                
                resolved = path_obj.resolve()
                
                if not allow_symlinks and path_obj.is_symlink():
                    return False, "Symlinks not allowed"
            else:
                resolved = path_obj.absolute()
        except (OSError, RuntimeError) as e:
            return False, f"Path resolution error: {e}"
        
        # Check base directory restriction
        if base_dir:
            base_obj = Path(base_dir).resolve()
            try:
                resolved.relative_to(base_obj)
            except ValueError:
                return False, f"Path must be within {base_dir}"
        
        return True, None
    
    def validate_filename(
        self,
        filename: str,
        allowed_extensions: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a filename.
        
        Args:
            filename: Filename to validate
            allowed_extensions: List of allowed extensions
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename or filename in (".", ".."):
            return False, "Invalid filename"
        
        if not self.SAFE_FILENAME_PATTERN.match(filename):
            return False, "Filename contains invalid characters"
        
        if allowed_extensions:
            ext = Path(filename).suffix.lower()
            if ext not in [e.lower() if e.startswith(".") else f".{e.lower()}" for e in allowed_extensions]:
                return False, f"Extension not allowed. Allowed: {', '.join(allowed_extensions)}"
        
        return True, None
    
    def validate_email(self, email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an email address.
        
        Args:
            email: Email to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(email, str):
            return False, "Email must be a string"
        
        if not self.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        
        # Additional checks
        if len(email) > 254:
            return False, "Email too long"
        
        local, _, domain = email.partition("@")
        if len(local) > 64:
            return False, "Email local part too long"
        
        return True, None
    
    def validate_ip(self, ip: str, version: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate an IP address.
        
        Args:
            ip: IP address to validate
            version: IP version (4 or 6), or None for either
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(ip, str):
            return False, "IP must be a string"
        
        if version == 4:
            if not self.IPV4_PATTERN.match(ip):
                return False, "Invalid IPv4 format"
            
            # Validate octets
            octets = ip.split(".")
            for octet in octets:
                if not 0 <= int(octet) <= 255:
                    return False, "IPv4 octet out of range"
            
        elif version == 6:
            if not self.IPV6_PATTERN.match(ip):
                return False, "Invalid IPv6 format"
        else:
            # Try both
            is_valid, _ = self.validate_ip(ip, version=4)
            if is_valid:
                return True, None
            is_valid, _ = self.validate_ip(ip, version=6)
            if is_valid:
                return True, None
            return False, "Invalid IP format"
        
        return True, None
    
    def validate_port(self, port: int) -> Tuple[bool, Optional[str]]:
        """
        Validate a port number.
        
        Args:
            port: Port number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(port, int):
            try:
                port = int(port)
            except (ValueError, TypeError):
                return False, "Port must be an integer"
        
        if not 0 <= port <= 65535:
            return False, "Port must be between 0 and 65535"
        
        if port < 1024:
            return True, "Port is a privileged port (< 1024)"
        
        return True, None
    
    def validate_url(
        self,
        url: str,
        allowed_schemes: Optional[List[str]] = None,
        allowed_hosts: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a URL.
        
        Args:
            url: URL to validate
            allowed_schemes: Allowed URL schemes
            allowed_hosts: Allowed hostnames
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(url, str):
            return False, "URL must be a string"
        
        try:
            parsed = urlparse(url)
        except Exception as e:
            return False, f"URL parsing error: {e}"
        
        if not parsed.scheme:
            return False, "URL missing scheme"
        
        if not parsed.netloc:
            return False, "URL missing host"
        
        if allowed_schemes and parsed.scheme.lower() not in [s.lower() for s in allowed_schemes]:
            return False, f"Scheme not allowed. Allowed: {', '.join(allowed_schemes)}"
        
        if allowed_hosts:
            host = parsed.hostname or ""
            if host.lower() not in [h.lower() for h in allowed_hosts]:
                return False, f"Host not allowed. Allowed: {', '.join(allowed_hosts)}"
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(url):
                return False, "URL contains dangerous pattern"
        
        return True, None
    
    def validate_integer(
        self,
        value: Any,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate an integer value.
        
        Args:
            value: Value to validate
            min_value: Minimum value
            max_value: Maximum value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            return False, "Value must be an integer"
        
        if min_value is not None and int_value < min_value:
            return False, f"Value must be >= {min_value}"
        
        if max_value is not None and int_value > max_value:
            return False, f"Value must be <= {max_value}"
        
        return True, None
    
    def validate_dict(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Dict[str, Any]],
    ) -> Tuple[bool, List[str]]:
        """
        Validate a dictionary against a schema.
        
        Args:
            data: Dictionary to validate
            schema: Validation schema
            
        Returns:
            Tuple of (is_valid, list of error messages)
            
        Example schema:
            {
                "username": {"type": str, "required": True, "min_length": 3},
                "age": {"type": int, "min_value": 0, "max_value": 150},
            }
        """
        errors = []
        
        if not isinstance(data, dict):
            return False, ["Data must be a dictionary"]
        
        for field, rules in schema.items():
            required = rules.get("required", False)
            field_type = rules.get("type")
            
            # Check required fields
            if field not in data:
                if required:
                    errors.append(f"Missing required field: {field}")
                continue
            
            value = data[field]
            
            # Check type
            if field_type and not isinstance(value, field_type):
                errors.append(f"Field {field} must be {field_type.__name__}")
                continue
            
            # String validations
            if field_type == str:
                if "min_length" in rules and len(value) < rules["min_length"]:
                    errors.append(f"Field {field} too short")
                if "max_length" in rules and len(value) > rules["max_length"]:
                    errors.append(f"Field {field} too long")
            
            # Integer validations
            if field_type == int:
                if "min_value" in rules and value < rules["min_value"]:
                    errors.append(f"Field {field} below minimum")
                if "max_value" in rules and value > rules["max_value"]:
                    errors.append(f"Field {field} above maximum")
        
        return len(errors) == 0, errors
    
    def is_safe_command(self, command: str, allowed_commands: Optional[List[str]] = None) -> bool:
        """
        Check if a command is safe to execute.
        
        Args:
            command: Command to check
            allowed_commands: List of allowed commands
            
        Returns:
            True if safe
        """
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(command):
                return False
        
        # Check against allowed list
        if allowed_commands:
            cmd_base = command.split()[0] if command.split() else ""
            if cmd_base not in allowed_commands:
                return False
        
        return True
    
    def generate_safe_token(self, length: int = 32) -> str:
        """
        Generate a safe random token.
        
        Args:
            length: Token length
            
        Returns:
            Safe token string
        """
        import secrets
        
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))
