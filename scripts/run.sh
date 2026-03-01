#!/bin/bash
#
# Bastion Execution Wrapper
#
# Provides a unified interface to run Bastion tools.
#
# Usage: ./scripts/run.sh [command] [options]
#
# Commands:
#   check       Run security checks (default)
#   validate    Validate input or configuration
#   report      Generate a report
#   help        Show help information
#
# Options:
#   -l, --level     Check level: basic, intermediate, advanced
#   -f, --format    Output format: json, text
#   -o, --output    Output file path
#   -c, --config    Configuration file path
#   -v, --verbose   Enable verbose output
#   -h, --help      Show this help message
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
COMMAND="check"
LEVEL="basic"
FORMAT="json"
OUTPUT=""
CONFIG=""
VERBOSE=""

# Print usage
usage() {
    cat << EOF
Bastion Security Toolkit

Usage: $0 [command] [options]

Commands:
  check       Run security checks (default)
  validate    Validate input or configuration
  report      Generate a report
  help        Show this help message

Options:
  -l, --level LEVEL     Check level: basic, intermediate, advanced
  -f, --format FORMAT   Output format: json, text
  -o, --output FILE     Output file path
  -c, --config FILE     Configuration file path
  -v, --verbose         Enable verbose output
  -h, --help            Show this help message

Examples:
  $0 check --level advanced --format json
  $0 validate -c config.yaml
  $0 report -o reports/security-report.json

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        check|validate|report)
            COMMAND="$1"
            shift
            ;;
        -l|--level)
            LEVEL="$2"
            shift 2
            ;;
        -f|--format)
            FORMAT="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Change to project directory
cd "$PROJECT_DIR"

# Check Python availability
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 is required but not installed.${NC}"
    exit 1
fi

# Build command arguments
PYTHON_ARGS=()

if [ -n "$CONFIG" ]; then
    PYTHON_ARGS+=("--config" "$CONFIG")
fi

PYTHON_ARGS+=("--level" "$LEVEL")
PYTHON_ARGS+=("--format" "$FORMAT")

if [ -n "$OUTPUT" ]; then
    PYTHON_ARGS+=("--output" "$OUTPUT")
fi

if [ -n "$VERBOSE" ]; then
    PYTHON_ARGS+=("$VERBOSE")
fi

# Execute based on command
case $COMMAND in
    check)
        echo -e "${BLUE}Running Bastion security check (level: $LEVEL)...${NC}"
        echo ""
        python3 -m src.bastion "${PYTHON_ARGS[@]}"
        ;;
    
    validate)
        echo -e "${BLUE}Validating configuration...${NC}"
        echo ""
        python3 -c "
import sys
sys.path.insert(0, '.')
from src.config import Config

config_path = '$CONFIG' if '$CONFIG' else None
config = Config(config_path)
valid, errors = config.validate()

if valid:
    print('Configuration is valid')
    sys.exit(0)
else:
    print('Configuration errors:')
    for error in errors:
        print(f'  - {error}')
    sys.exit(1)
"
        ;;
    
    report)
        echo -e "${BLUE}Generating Bastion report...${NC}"
        echo ""
        python3 -m src.bastion "${PYTHON_ARGS[@]}"
        ;;
    
    help)
        usage
        exit 0
        ;;
    
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        usage
        exit 1
        ;;
esac

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}Command completed successfully.${NC}"
else
    echo -e "${YELLOW}Command completed with warnings or errors.${NC}"
fi

exit $exit_code
