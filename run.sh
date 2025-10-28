#!/bin/bash

# Address Cleanser Run Script
# This script provides a wrapper for running the Address Cleanser tool with proper logging

set -euo pipefail

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create necessary directories
mkdir -p logs out

# Set up logging
LOG_FILE="logs/$(date +%F).log"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to show usage
show_usage() {
    echo "Address Cleanser Run Script"
    echo ""
    echo "Usage: $0 [OPTIONS] COMMAND [COMMAND_OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  single    Process a single address"
    echo "  batch     Process addresses from a CSV file"
    echo ""
    echo "Options:"
    echo "  --log-level LEVEL    Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    echo "  --log-file FILE      Set log file path"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 single --single '123 Main Street, Austin, TX 78701'"
    echo "  $0 batch --input addresses.csv --output cleaned.csv --format csv"
    echo "  $0 --log-level DEBUG batch --input large_file.csv --output results.xlsx --format excel"
    echo ""
    echo "For more detailed help, run:"
    echo "  python3 cli.py --help"
    echo "  python3 cli.py single --help"
    echo "  python3 cli.py batch --help"
}

# Parse command line arguments
CLI_ARGS=()
LOG_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --log-level)
            LOG_LEVEL="$2"
            LOG_ARGS+=(--log-level "$2")
            shift 2
            ;;
        --log-file)
            LOG_FILE="$2"
            LOG_ARGS+=(--log-file "$2")
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            CLI_ARGS+=("$1")
            shift
            ;;
    esac
done

# Check if command is provided
if [ ${#CLI_ARGS[@]} -eq 0 ]; then
    echo "Error: No command provided"
    echo ""
    show_usage
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    log "ERROR: Python 3 is required but not installed"
    exit 1
fi

# Check if cli.py exists
if [ ! -f "cli.py" ]; then
    log "ERROR: cli.py not found in current directory"
    exit 1
fi

# Log the start of execution
log "Starting Address Cleanser with command: ${CLI_ARGS[*]}"
log "Log level: $LOG_LEVEL"
log "Log file: $LOG_FILE"

# Run the CLI with proper error handling
if python3 cli.py "${LOG_ARGS[@]}" "${CLI_ARGS[@]}" 2>&1 | tee -a "$LOG_FILE"; then
    log "Address Cleanser completed successfully"
    exit 0
else
    log "ERROR: Address Cleanser failed"
    exit 1
fi
