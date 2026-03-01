#!/bin/bash
#
# Bastion Setup Script
# 
# Installs dependencies and configures the Bastion toolkit.
#
# Usage: ./scripts/setup.sh [options]
#
# Options:
#   --skip-python    Skip Python dependency installation
#   --skip-node      Skip Node.js dependency installation
#   --skip-dotnet    Skip .NET dependency installation
#   --dry-run        Show what would be done without making changes
#   --help           Show this help message
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Flags
SKIP_PYTHON=false
SKIP_NODE=false
SKIP_DOTNET=false
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-python)
            SKIP_PYTHON=true
            shift
            ;;
        --skip-node)
            SKIP_NODE=true
            shift
            ;;
        --skip-dotnet)
            SKIP_DOTNET=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help)
            head -15 "$0" | tail -12
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Execute or print command based on dry-run
exec_cmd() {
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would execute: $*"
    else
        "$@"
    fi
}

echo "========================================"
echo "  Bastion Setup Script"
echo "========================================"
echo ""

# Check Python
if [ "$SKIP_PYTHON" = false ]; then
    log_info "Checking Python installation..."
    
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        log_success "Found: $PYTHON_VERSION"
        
        # Check version >= 3.8
        PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
        if [ "$PYTHON_MINOR" -lt 8 ]; then
            log_warning "Python 3.8+ recommended, found 3.$PYTHON_MINOR"
        fi
        
        # Install Python dependencies
        if [ -f "$PROJECT_DIR/requirements.txt" ]; then
            log_info "Installing Python dependencies..."
            exec_cmd python3 -m pip install --upgrade pip
            exec_cmd python3 -m pip install -r "$PROJECT_DIR/requirements.txt"
            log_success "Python dependencies installed"
        else
            log_warning "requirements.txt not found"
        fi
    else
        log_warning "Python3 not found. Please install Python 3.8+"
    fi
else
    log_info "Skipping Python setup (--skip-python)"
fi

echo ""

# Check Node.js
if [ "$SKIP_NODE" = false ]; then
    log_info "Checking Node.js installation..."
    
    if command_exists node; then
        NODE_VERSION=$(node --version 2>&1)
        log_success "Found: Node $NODE_VERSION"
        
        # Check npm
        if command_exists npm; then
            NPM_VERSION=$(npm --version 2>&1)
            log_success "Found: npm $NPM_VERSION"
            
            # Install Node dependencies if package.json exists
            if [ -f "$PROJECT_DIR/package.json" ]; then
                log_info "Installing Node.js dependencies..."
                exec_cmd npm install --prefix "$PROJECT_DIR"
                log_success "Node.js dependencies installed"
            fi
        else
            log_warning "npm not found"
        fi
    else
        log_info "Node.js not found (optional for JS helpers)"
    fi
else
    log_info "Skipping Node.js setup (--skip-node)"
fi

echo ""

# Check .NET
if [ "$SKIP_DOTNET" = false ]; then
    log_info "Checking .NET installation..."
    
    if command_exists dotnet; then
        DOTNET_VERSION=$(dotnet --version 2>&1)
        log_success "Found: .NET $DOTNET_VERSION"
        
        # Restore NuGet packages if .csproj exists
        CSPROJ_FILE=$(find "$PROJECT_DIR/csharp" -name "*.csproj" 2>/dev/null | head -1)
        if [ -n "$CSPROJ_FILE" ]; then
            log_info "Restoring .NET dependencies..."
            exec_cmd dotnet restore "$CSPROJ_FILE"
            log_success ".NET dependencies restored"
        fi
    else
        log_info ".NET SDK not found (optional for C# module)"
    fi
else
    log_info "Skipping .NET setup (--skip-dotnet)"
fi

echo ""

# Create directories
log_info "Creating required directories..."
for dir in reports logs data; do
    DIR_PATH="$PROJECT_DIR/$dir"
    if [ ! -d "$DIR_PATH" ]; then
        if [ "$DRY_RUN" = true ]; then
            log_info "[DRY-RUN] Would create directory: $DIR_PATH"
        else
            mkdir -p "$DIR_PATH"
            log_success "Created: $dir/"
        fi
    else
        log_info "Exists: $dir/"
    fi
done

echo ""

# Create default config if not exists
if [ ! -f "$PROJECT_DIR/config.yaml" ]; then
    log_info "Creating default configuration..."
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would create: config.yaml"
    else
        cat > "$PROJECT_DIR/config.yaml" << 'EOF'
# Bastion Configuration
# See README.md for options

bastion:
  log_level: INFO
  output_dir: ./reports
  modules:
    - core

security:
  check_level: basic
  fail_on_warning: false

logging:
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: bastion.log
  max_size_mb: 10
  backup_count: 5
EOF
        log_success "Created: config.yaml"
    fi
else
    log_info "Exists: config.yaml"
fi

echo ""

# Set permissions
log_info "Setting script permissions..."
for script in "$SCRIPT_DIR"/*.sh; do
    if [ -f "$script" ]; then
        if [ "$DRY_RUN" = true ]; then
            log_info "[DRY-RUN] Would chmod +x: $script"
        else
            chmod +x "$script"
        fi
    fi
done
log_success "Permissions set"

echo ""
echo "========================================"
if [ "$DRY_RUN" = true ]; then
    log_info "Dry run complete. No changes were made."
else
    log_success "Setup complete!"
fi
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Review config.yaml and customize settings"
echo "  2. Run: ./scripts/run.sh --help"
echo "  3. Or: python3 -m src.bastion --help"
echo ""
