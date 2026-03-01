# Bastion

A modular, extensible toolkit for security automation and system hardening.

## Overview

Bastion is designed as a collection of interchangeable modules that can be used independently or together to provide comprehensive security utilities.

## Features

- **Modular Architecture**: Each component is self-contained and can be used independently
- **Multi-language Support**: Core functionality in Python, with helpers in JavaScript, Shell, and C#
- **Configuration-driven**: YAML-based configuration for easy customization
- **Logging & Auditing**: Comprehensive logging for security operations
- **Validation**: Input validation and sanitization utilities

## Project Structure

```
Bastion/
├── README.md              # This file
├── LICENSE                # MIT License
├── requirements.txt       # Python dependencies
├── config.yaml            # Main configuration
├── src/
│   ├── __init__.py
│   ├── bastion.py         # Core module
│   ├── config.py          # Configuration handler
│   ├── logger.py          # Logging utilities
│   └── validator.py       # Input validation
├── scripts/
│   ├── setup.sh           # Installation script
│   └── run.sh             # Execution wrapper
├── js/
│   └── bastion-helper.js  # JavaScript utilities
└── csharp/
    └── BastionCore.cs     # C# module example
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+ (for JS helpers)
- .NET 6+ (for C# module)

### Installation

```bash
# Clone and setup
git clone <repository>
cd Bastion
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Usage

```bash
# Run via shell wrapper
./scripts/run.sh --help

# Or use Python directly
python -m src.bastion --help
```

## Modules

### Core (Python)

The main `bastion.py` module provides:
- System information gathering
- Security baseline checks
- Report generation

### Utilities

- **config.py**: YAML configuration parsing and validation
- **logger.py**: Structured logging with multiple output formats
- **validator.py**: Input validation and sanitization

### JavaScript Helper

`bastion-helper.js` provides:
- JSON manipulation utilities
- File system operations
- Network helpers

### C# Module

`BastionCore.cs` demonstrates:
- .NET integration patterns
- Windows-specific security checks

## Configuration

Edit `config.yaml` to customize:

```yaml
bastion:
  log_level: INFO
  output_dir: ./reports
  modules:
    - core
    - validator
```

## License

MIT License - See LICENSE file for details.
