#!/usr/bin/env python3
"""
Logger Module

Provides structured logging with multiple output formats and handlers.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union


class Logger:
    """
    Structured logger for Bastion.
    
    Supports multiple output formats (text, JSON) and handlers
    (console, file).
    
    Attributes:
        name: Logger name
        level: Logging level
        output_dir: Directory for log files
    """
    
    LOG_LEVELS = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    def __init__(
        self,
        name: str = "bastion",
        level: str = "INFO",
        output_dir: Optional[Union[str, Path]] = None,
        log_file: Optional[str] = None,
        format_type: str = "text",
    ):
        """
        Initialize logger.
        
        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            output_dir: Directory for log files
            log_file: Log file name
            format_type: Output format (text, json)
        """
        self.name = name
        self.level = level
        self.output_dir = Path(output_dir) if output_dir else None
        self.log_file = log_file
        self.format_type = format_type
        
        self._logger = logging.getLogger(name)
        self._logger.setLevel(self.LOG_LEVELS.get(level.upper(), logging.INFO))
        
        # Clear existing handlers
        self._logger.handlers.clear()
        
        # Add console handler
        self._add_console_handler()
        
        # Add file handler if output_dir specified
        if self.output_dir and self.log_file:
            self._add_file_handler()
    
    def _add_console_handler(self) -> None:
        """Add console output handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.LOG_LEVELS.get(self.level.upper(), logging.INFO))
        
        if self.format_type == "json":
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
    
    def _add_file_handler(self) -> None:
        """Add file output handler."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            log_path = self.output_dir / self.log_file
            
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)  # Log everything to file
            
            if self.format_type == "json":
                formatter = JsonFormatter()
            else:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
            
        except Exception as e:
            self._logger.warning(f"Could not create file handler: {e}")
    
    def set_level(self, level: str) -> None:
        """
        Set logging level.
        
        Args:
            level: New logging level
        """
        self.level = level
        log_level = self.LOG_LEVELS.get(level.upper(), logging.INFO)
        self._logger.setLevel(log_level)
        
        for handler in self._logger.handlers:
            handler.setLevel(log_level)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """
        Internal log method with extra context support.
        
        Args:
            level: Logging level
            message: Log message
            **kwargs: Extra context to include
        """
        if kwargs and self.format_type == "json":
            # For JSON format, include extra context
            extra = {"context": kwargs}
            self._logger.log(level, message, extra=extra)
        else:
            # For text format, append context to message
            if kwargs:
                context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
                message = f"{message} [{context_str}]"
            self._logger.log(level, message)
    
    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Log a structured event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
        }
        
        if self.format_type == "json":
            self.info(json.dumps(event))
        else:
            self.info(f"[EVENT {event_type}] {json.dumps(data)}")
    
    def close(self) -> None:
        """Close all handlers."""
        for handler in self._logger.handlers:
            handler.close()
        self._logger.handlers.clear()


class JsonFormatter(logging.Formatter):
    """
    JSON log formatter.
    
    Outputs log records as JSON for easy parsing.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record
            
        Returns:
            JSON formatted string
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra context if present
        if hasattr(record, "context"):
            log_data["context"] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


class AuditLogger:
    """
    Specialized logger for security audit trails.
    
    Provides immutable audit logging with tamper-evident features.
    """
    
    def __init__(self, output_path: Union[str, Path]):
        """
        Initialize audit logger.
        
        Args:
            output_path: Path to audit log file
        """
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write header if file doesn't exist
        if not self.output_path.exists():
            self._write_header()
    
    def _write_header(self) -> None:
        """Write audit log header."""
        header = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "format": "jsonl",  # JSON Lines
        }
        
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(f"# AUDIT LOG: {json.dumps(header)}\n")
    
    def log(
        self,
        action: str,
        user: str,
        resource: str,
        result: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log an audit event.
        
        Args:
            action: Action performed
            user: User who performed action
            resource: Resource affected
            result: Result of action (success, failure, denied)
            details: Additional details
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "user": user,
            "resource": resource,
            "result": result,
            "details": details or {},
        }
        
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    
    def read_entries(self, limit: int = 100) -> list[Dict[str, Any]]:
        """
        Read recent audit entries.
        
        Args:
            limit: Maximum entries to return
            
        Returns:
            List of audit entries
        """
        entries = []
        
        try:
            with open(self.output_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("#"):
                        continue
                    
                    try:
                        entry = json.loads(line.strip())
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
                    
                    if len(entries) >= limit:
                        break
        except FileNotFoundError:
            pass
        
        return entries
