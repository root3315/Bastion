#!/usr/bin/env python3
"""
Bastion Core Module

Main entry point for the Bastion security toolkit.
Provides system information gathering, security checks, and reporting.
"""

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import Config
from .logger import Logger
from .validator import Validator


class Bastion:
    """
    Main Bastion class providing core security toolkit functionality.
    
    Attributes:
        config: Configuration instance
        logger: Logger instance
        validator: Validator instance
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Bastion with optional configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config = Config(config_path)
        self.logger = Logger(
            level=self.config.get("log_level", "INFO"),
            output_dir=self.config.get("output_dir", "./reports")
        )
        self.validator = Validator()
        self.start_time = datetime.now()
        
    def get_system_info(self) -> Dict[str, Any]:
        """
        Gather comprehensive system information.
        
        Returns:
            Dictionary containing system details
        """
        self.logger.info("Gathering system information")
        
        info = {
            "timestamp": datetime.now().isoformat(),
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "architecture": platform.architecture()[0],
            },
            "python": {
                "version": platform.python_version(),
                "implementation": platform.python_implementation(),
                "compiler": platform.python_compiler(),
            },
            "network": {
                "hostname": socket.gethostname(),
                "fqdn": socket.getfqdn(),
            },
            "environment": {
                "user": os.getenv("USER", os.getenv("USERNAME", "unknown")),
                "home": os.getenv("HOME", os.getenv("USERPROFILE", "unknown")),
                "cwd": os.getcwd(),
            }
        }
        
        self.logger.debug(f"System info collected: {json.dumps(info, indent=2)}")
        return info
    
    def run_security_check(self, check_type: str = "basic") -> Dict[str, Any]:
        """
        Execute security baseline checks.
        
        Args:
            check_type: Type of check to run (basic, intermediate, advanced)
            
        Returns:
            Dictionary containing check results
        """
        self.logger.info(f"Running {check_type} security check")
        
        results = {
            "check_type": check_type,
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "summary": {
                "passed": 0,
                "failed": 0,
                "warnings": 0,
            }
        }
        
        # Basic checks
        basic_checks = [
            self._check_root_access,
            self._check_python_version,
            self._check_temp_permissions,
        ]
        
        # Intermediate checks
        intermediate_checks = basic_checks + [
            self._check_environment_vars,
            self._check_file_permissions,
        ]
        
        # Advanced checks
        advanced_checks = intermediate_checks + [
            self._check_network_services,
            self._check_installed_packages,
        ]
        
        check_mapping = {
            "basic": basic_checks,
            "intermediate": intermediate_checks,
            "advanced": advanced_checks,
        }
        
        checks_to_run = check_mapping.get(check_type, basic_checks)
        
        for check in checks_to_run:
            try:
                result = check()
                results["checks"].append(result)
                
                status = result.get("status", "unknown")
                if status == "passed":
                    results["summary"]["passed"] += 1
                elif status == "failed":
                    results["summary"]["failed"] += 1
                elif status == "warning":
                    results["summary"]["warnings"] += 1
                    
            except Exception as e:
                self.logger.error(f"Check {check.__name__} failed: {str(e)}")
                results["checks"].append({
                    "name": check.__name__,
                    "status": "error",
                    "message": str(e),
                })
                results["summary"]["failed"] += 1
        
        self.logger.info(
            f"Security check complete: {results['summary']['passed']} passed, "
            f"{results['summary']['failed']} failed, {results['summary']['warnings']} warnings"
        )
        
        return results
    
    def _check_root_access(self) -> Dict[str, Any]:
        """Check if running as root/admin."""
        is_root = os.geteuid() == 0 if hasattr(os, "geteuid") else False
        return {
            "name": "root_access",
            "status": "warning" if is_root else "passed",
            "message": "Running as root" if is_root else "Not running as root",
            "recommendation": "Avoid running as root unless necessary" if is_root else None,
        }
    
    def _check_python_version(self) -> Dict[str, Any]:
        """Check Python version meets minimum requirements."""
        min_version = (3, 8)
        current = sys.version_info[:2]
        passed = current >= min_version
        return {
            "name": "python_version",
            "status": "passed" if passed else "failed",
            "message": f"Python {'.'.join(map(str, current))}",
            "recommendation": f"Upgrade to Python {'.'.join(map(str, min_version))}+" if not passed else None,
        }
    
    def _check_temp_permissions(self) -> Dict[str, Any]:
        """Check temp directory permissions."""
        temp_dir = Path("/tmp" if platform.system() != "Windows" else os.getenv("TEMP", "."))
        try:
            if temp_dir.exists():
                stat_info = temp_dir.stat()
                is_writable = os.access(temp_dir, os.W_OK)
                return {
                    "name": "temp_permissions",
                    "status": "passed" if is_writable else "warning",
                    "message": f"Temp dir: {temp_dir}, writable: {is_writable}",
                }
        except Exception as e:
            pass
        return {
            "name": "temp_permissions",
            "status": "warning",
            "message": "Could not verify temp directory",
        }
    
    def _check_environment_vars(self) -> Dict[str, Any]:
        """Check for sensitive environment variables."""
        sensitive_patterns = ["PASSWORD", "SECRET", "KEY", "TOKEN"]
        found = []
        for key in os.environ:
            for pattern in sensitive_patterns:
                if pattern in key.upper():
                    found.append(key)
                    break
        return {
            "name": "environment_vars",
            "status": "warning" if found else "passed",
            "message": f"Found {len(found)} sensitive env vars" if found else "No obvious sensitive env vars",
            "details": found if found else None,
        }
    
    def _check_file_permissions(self) -> Dict[str, Any]:
        """Check file permissions in current directory."""
        issues = []
        try:
            for item in Path(".").iterdir():
                try:
                    mode = item.stat().st_mode
                    # Check for world-writable files
                    if mode & 0o002:
                        issues.append(str(item))
                except (OSError, PermissionError):
                    continue
        except Exception:
            pass
        return {
            "name": "file_permissions",
            "status": "warning" if issues else "passed",
            "message": f"Found {len(issues)} world-writable items" if issues else "No world-writable files",
            "details": issues if issues else None,
        }
    
    def _check_network_services(self) -> Dict[str, Any]:
        """Check for listening network services."""
        services = []
        try:
            result = subprocess.run(
                ["ss", "-tuln"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            services = [line for line in lines if line.strip()]
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return {
            "name": "network_services",
            "status": "info",
            "message": f"Found {len(services)} listening services",
            "details": services[:10] if services else None,  # Limit output
        }
    
    def _check_installed_packages(self) -> Dict[str, Any]:
        """Check installed Python packages."""
        packages = []
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            packages = json.loads(result.stdout)
        except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
            pass
        return {
            "name": "installed_packages",
            "status": "info",
            "message": f"Found {len(packages)} installed packages",
            "details": packages[:20] if packages else None,  # Limit output
        }
    
    def generate_report(self, data: Dict[str, Any], output_format: str = "json") -> str:
        """
        Generate a formatted report from check results.
        
        Args:
            data: Data to include in report
            output_format: Output format (json, text)
            
        Returns:
            Formatted report string
        """
        self.logger.info(f"Generating {output_format} report")
        
        if output_format == "json":
            return json.dumps(data, indent=2, default=str)
        
        # Text format
        lines = [
            "=" * 60,
            "BASTION SECURITY REPORT",
            "=" * 60,
            f"Generated: {datetime.now().isoformat()}",
            "",
        ]
        
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"[{key.upper()}]")
                for k, v in value.items():
                    lines.append(f"  {k}: {v}")
                lines.append("")
            elif isinstance(value, list):
                lines.append(f"[{key.upper()}]")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(f"  - {item.get('name', 'unknown')}: {item.get('status', 'unknown')}")
                    else:
                        lines.append(f"  - {item}")
                lines.append("")
            else:
                lines.append(f"{key}: {value}")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Main entry point for CLI execution.
        
        Args:
            args: Command line arguments
            
        Returns:
            Exit code
        """
        parser = argparse.ArgumentParser(
            prog="bastion",
            description="Bastion Security Toolkit",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        
        parser.add_argument(
            "-c", "--config",
            help="Path to configuration file",
        )
        parser.add_argument(
            "-l", "--level",
            choices=["basic", "intermediate", "advanced"],
            default="basic",
            help="Security check level",
        )
        parser.add_argument(
            "-f", "--format",
            choices=["json", "text"],
            default="json",
            help="Output format",
        )
        parser.add_argument(
            "-o", "--output",
            help="Output file path",
        )
        parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output",
        )
        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s 1.0.0",
        )
        
        parsed_args = parser.parse_args(args)
        
        if parsed_args.verbose:
            self.logger.set_level("DEBUG")
        
        # Run security check
        results = self.run_security_check(parsed_args.level)
        
        # Generate report
        report = self.generate_report(results, parsed_args.format)
        
        # Output
        if parsed_args.output:
            output_path = Path(parsed_args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report)
            self.logger.info(f"Report saved to {parsed_args.output}")
        else:
            print(report)
        
        # Return exit code based on failures
        return 1 if results["summary"]["failed"] > 0 else 0


def main():
    """CLI entry point."""
    bastion = Bastion()
    sys.exit(bastion.run())


if __name__ == "__main__":
    main()
