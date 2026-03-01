```markdown
# 🛡️ Bastion

> A modular, extensible toolkit for security automation and system hardening

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Node](https://img.shields.io/badge/node-16+-green.svg)
![.NET](https://img.shields.io/badge/.NET-6+-purple.svg)

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

**Bastion** is a comprehensive security toolkit designed for modern development environments. It provides a collection of interchangeable modules that can be used independently or together to deliver robust security utilities, system hardening capabilities, and automated security baseline checks.

Built with flexibility in mind, Bastion supports multiple programming languages including **Python**, **JavaScript**, **C#**, and **Shell**, making it adaptable to diverse technology stacks.

---

## ✨ Features

- **🧩 Modular Architecture** – Self-contained components that work independently or as a unified system
- **🌐 Multi-language Support** – Core in Python, with helpers in JavaScript, C#, and Shell scripts
- **⚙️ Configuration-driven** – YAML-based configuration with environment variable overrides
- **📝 Comprehensive Logging** – Structured logging with JSON and text output formats
- **✅ Input Validation** – Robust validation and sanitization utilities for security-critical operations
- **🔒 Security Checks** – Automated baseline security checks at multiple levels (basic, intermediate, advanced)
- **📊 Report Generation** – Generate detailed security reports in JSON or human-readable text format
- **🛠️ Cross-platform** – Works on Linux, macOS, and Windows

---

## 📁 Project Structure

```
Bastion/
├── README.md              # Project documentation
├── LICENSE                # MIT License
├── requirements.txt       # Python dependencies
├── package.json           # Node.js configuration
├── config.yaml            # Main configuration file
├── src/
│   ├── __init__.py        # Package initialization
│   ├── bastion.py         # Core security module
│   ├── config.py          # Configuration handler
│   ├── logger.py          # Logging utilities
│   └── validator.py       # Input validation module
├── scripts/
│   ├── setup.sh           # Installation script
│   └── run.sh             # Execution wrapper
├── js/
│   └── bastion-helper.js  # JavaScript utility helpers
└── csharp/
    ├── BastionCore.cs     # C# core module
    └── BastionCore.csproj # .NET project file
```

---

## 🚀 Installation

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.8+ | Core functionality |
| Node.js | 16+ | JavaScript helpers |
| .NET SDK | 6.0+ | C# module |

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd Bastion

# Run the setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Manual Installation

#### Python Dependencies

```bash
pip install -r requirements.txt
```

#### Node.js Dependencies

```bash
npm install
```

#### .NET Dependencies

```bash
dotnet restore csharp/BastionCore.csproj
```

---

## 💻 Usage

### CLI Interface

```bash
# Using the shell wrapper
./scripts/run.sh check --level advanced --format json

# Using Python directly
python3 -m src.bastion --help

# Validate configuration
./scripts/run.sh validate -c config.yaml

# Generate a report
./scripts/run.sh report -o reports/security-report.json
```

### Command Reference

| Command | Description |
|---------|-------------|
| `check` | Run security baseline checks |
| `validate` | Validate configuration files |
| `report` | Generate security reports |
| `help` | Display help information |

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--level` | `-l` | Check level: `basic`, `intermediate`, `advanced` |
| `--format` | `-f` | Output format: `json`, `text` |
| `--output` | `-o` | Output file path |
| `--config` | `-c` | Configuration file path |
| `--verbose` | `-v` | Enable verbose/DEBUG output |
| `--help` | `-h` | Show help message |

### Programmatic Usage

#### Python

```python
from src import Bastion, Config, Logger, Validator

# Initialize with configuration
bastion = Bastion(config_path="config.yaml")

# Gather system information
sys_info = bastion.get_system_info()

# Run security checks
results = bastion.run_security_check(level="advanced")

# Generate report
report = bastion.generate_report(results, output_format="json")
print(report)
```

#### JavaScript

```javascript
const { BastionHelper, createHelper } = require('./js/bastion-helper');

// Create helper instance
const helper = createHelper({ logLevel: 'info', outputDir: './reports' });

// Generate secure token
const token = helper.generateToken(32);

// Validate JSON
const result = helper.validateJson(data, schema);

// Make HTTP request
const response = await helper.fetch('https://api.example.com/data');
```

#### C#

```csharp
using Bastion;

// Initialize Bastion
var bastion = new BastionCore("config.yaml");

// Get system information
var sysInfo = bastion.GetSystemInfo();

// Run security checks
var results = bastion.RunSecurityCheck("advanced");

// Generate report
var report = bastion.GenerateReport(results, "text");
Console.WriteLine(report);
```

---

## 📚 API Documentation

### Python Modules

#### `Bastion` Class

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `__init__` | `config_path: str` | - | Initialize with optional config |
| `get_system_info` | - | `Dict` | Gather system information |
| `run_security_check` | `check_type: str` | `Dict` | Execute security checks |
| `generate_report` | `data: Dict, format: str` | `str` | Generate formatted report |

#### `Validator` Class

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `validate_string` | `value, min_length, max_length, ...` | `Tuple[bool, str]` | Validate string input |
| `validate_path` | `path, must_exist, base_dir, ...` | `Tuple[bool, str]` | Validate file paths |
| `validate_email` | `email: str` | `Tuple[bool, str]` | Validate email format |
| `validate_ip` | `ip: str, version: int` | `Tuple[bool, str]` | Validate IP addresses |
| `validate_url` | `url, allowed_schemes, ...` | `Tuple[bool, str]` | Validate URLs |
| `sanitize_string` | `value, remove_chars, ...` | `str` | Sanitize input strings |

#### `Logger` Class

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `debug/info/warning/error` | `message: str` | - | Log at various levels |
| `set_level` | `level: str` | - | Set logging level |
| `log_event` | `event_type, data` | - | Log structured events |

#### `Config` Class

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `get` | `key: str, default: Any` | `Any` | Get config value |
| `set` | `key: str, value: Any` | - | Set config value |
| `validate` | - | `Tuple[bool, list]` | Validate configuration |
| `save` | `path: str` | `bool` | Save configuration |

### JavaScript API

#### `BastionHelper` Class

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `validateJson` | `data, schema` | `Object` | Validate JSON data |
| `generateToken` | `length: number` | `string` | Generate secure token |
| `hash` | `data, algorithm` | `string` | Hash data |
| `readFile/writeFile` | `filePath, options` | `Object` | File operations |
| `fetch` | `url, options` | `Promise` | HTTP requests |
| `validateEmail` | `email: string` | `boolean` | Validate email |
| `validateIp` | `ip, version` | `boolean` | Validate IP |
| `retry` | `fn, options` | `Promise` | Retry with backoff |

### C# API

#### `BastionCore` Class

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `GetSystemInfo` | - | `SystemInfo` | Gather system info |
| `RunSecurityCheck` | `level: string` | `SecurityResults` | Run security checks |
| `GenerateReport` | `results, format` | `string` | Generate report |
| `IsElevated` | - | `bool` | Check admin privileges |

---

## ⚙️ Configuration

Edit `config.yaml` to customize Bastion behavior:

```yaml
# Main Bastion settings
bastion:
  log_level: INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
  output_dir: ./reports              # Output directory for reports
  modules:
    - core                           # Enable core module
    - validator                      # Enable validator module
  max_retries: 3                     # Connection retry limit
  timeout: 30                        # Timeout in seconds

# Security check settings
security:
  check_level: basic                 # basic, intermediate, advanced
  fail_on_warning: false             # Exit code on warnings
  ignore_patterns:                   # Patterns to ignore
    - "*.log"
    - "*.tmp"
    - ".git/*"

# Logging configuration
logging:
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: bastion.log
  max_size_mb: 10
  backup_count: 5
```

### Environment Variable Overrides

| Environment Variable | Config Path | Description |
|---------------------|-------------|-------------|
| `BASTION_LOG_LEVEL` | `bastion.log_level` | Set logging level |
| `BASTION_OUTPUT_DIR` | `bastion.output_dir` | Set output directory |
| `BASTION_CHECK_LEVEL` | `security.check_level` | Set check level |

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Getting Started

1. **Fork** the repository
2. **Clone** your fork: `git clone <your-fork-url>`
3. **Create a branch**: `git checkout -b feature/your-feature`
4. **Make changes** and test thoroughly
5. **Commit** with clear messages
6. **Push** and create a Pull Request

### Code Style

- Follow existing code conventions in each language
- Add tests for new functionality
- Document public APIs
- Update README for user-facing changes

### Reporting Issues

- Use the issue tracker for bugs and feature requests
- Include steps to reproduce for bugs
- Provide environment details (OS, versions)

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
Copyright (c) 2026 Bastion Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

<div align="center">

**Built with ❤️ by the Bastion Team**

[🔝 Back to Top](#-bastion)

</div>
```
