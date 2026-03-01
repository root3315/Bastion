#!/usr/bin/env python3
"""
Configuration Handler Module

Provides YAML configuration parsing, validation, and access utilities.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class Config:
    """
    Configuration handler for Bastion.
    
    Supports YAML configuration files with fallback to defaults.
    
    Attributes:
        config_path: Path to configuration file
        data: Configuration data dictionary
    """
    
    DEFAULTS = {
        "bastion": {
            "log_level": "INFO",
            "output_dir": "./reports",
            "modules": ["core"],
            "max_retries": 3,
            "timeout": 30,
        },
        "security": {
            "check_level": "basic",
            "fail_on_warning": False,
            "ignore_patterns": [],
        },
        "logging": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "bastion.log",
            "max_size_mb": 10,
            "backup_count": 5,
        }
    }
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize configuration handler.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path) if config_path else None
        self.data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.
        
        Returns:
            Merged configuration dictionary
        """
        config = self.DEFAULTS.copy()
        
        if self.config_path and self.config_path.exists():
            try:
                if not YAML_AVAILABLE:
                    raise ImportError("PyYAML not installed")
                
                with open(self.config_path, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f) or {}
                
                # Deep merge
                config = self._deep_merge(config, file_config)
                
            except Exception as e:
                # Log error but continue with defaults
                print(f"Warning: Could not load config from {self.config_path}: {e}")
        
        # Override with environment variables
        config = self._apply_env_overrides(config)
        
        return config
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """
        Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Dictionary to merge on top
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict) -> Dict:
        """
        Apply environment variable overrides.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Updated configuration dictionary
        """
        # Example: BASTION_LOG_LEVEL=DEBUG overrides bastion.log_level
        env_mappings = {
            "BASTION_LOG_LEVEL": ("bastion", "log_level"),
            "BASTION_OUTPUT_DIR": ("bastion", "output_dir"),
            "BASTION_CHECK_LEVEL": ("security", "check_level"),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                if section not in config:
                    config[section] = {}
                config[section][key] = value
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., "bastion.log_level")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., "bastion.log_level")
            value: Value to set
        """
        keys = key.split(".")
        config = self.data
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, path: Optional[Union[str, Path]] = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            path: Path to save to (uses original path if None)
            
        Returns:
            True if saved successfully
        """
        save_path = Path(path) if path else self.config_path
        
        if not save_path:
            return False
        
        try:
            if not YAML_AVAILABLE:
                raise ImportError("PyYAML not installed")
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, "w", encoding="utf-8") as f:
                yaml.dump(self.data, f, default_flow_style=False, sort_keys=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate configuration values.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = self.get("bastion.log_level", "INFO")
        if log_level.upper() not in valid_levels:
            errors.append(f"Invalid log level: {log_level}")
        
        # Validate output directory
        output_dir = self.get("bastion.output_dir", "./reports")
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create output directory: {e}")
        
        # Validate check level
        valid_levels = ["basic", "intermediate", "advanced"]
        check_level = self.get("security.check_level", "basic")
        if check_level not in valid_levels:
            errors.append(f"Invalid check level: {check_level}")
        
        return len(errors) == 0, errors
    
    def __repr__(self) -> str:
        return f"Config(path={self.config_path}, keys={list(self.data.keys())})"
    
    def __getitem__(self, key: str) -> Any:
        return self.get(key)
    
    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None
