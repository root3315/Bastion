"""
Bastion - Modular Security Toolkit

A collection of interchangeable modules for security automation.
"""

__version__ = "1.0.0"
__author__ = "Bastion Team"

from .bastion import Bastion
from .config import Config
from .logger import Logger
from .validator import Validator

__all__ = ["Bastion", "Config", "Logger", "Validator"]
