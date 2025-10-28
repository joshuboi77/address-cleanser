#!/bin/bash

# Address Cleanser Installation Script
# This script sets up the Address Cleanser tool and its dependencies

set -euo pipefail

echo "Address Cleanser Installation Script"
echo "===================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python $REQUIRED_VERSION or higher is required. Found Python $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION found"

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "Error: pip is required but not available."
    echo "Please install pip and try again."
    exit 1
fi

echo "✓ pip found"

# Create necessary directories
echo "Creating project directories..."
mkdir -p logs out

# Install dependencies
echo "Installing Python dependencies..."
if python3 -m pip install --user --break-system-packages -r requirements.txt; then
    echo "✓ Dependencies installed successfully"
else
    echo "Error: Failed to install dependencies"
    echo "You may need to install dependencies manually:"
    echo "  pip install usaddress pandas openpyxl click pytest pytest-cov tqdm"
    exit 1
fi

# Make scripts executable
chmod +x run.sh

# Run tests to verify installation
echo "Running tests to verify installation..."
if python3 -m pytest tests/ -q; then
    echo "✓ All tests passed"
else
    echo "Warning: Some tests failed. The installation may not be complete."
    echo "You can still try using the tool, but some features may not work correctly."
fi

echo ""
echo "Installation complete!"
echo ""
echo "Usage examples:"
echo "  # Process a single address"
echo "  python3 cli.py single --single '123 Main Street, Austin, TX 78701'"
echo ""
echo "  # Process a CSV file"
echo "  python3 cli.py batch --input addresses.csv --output cleaned.csv --format csv"
echo ""
echo "  # Process with validation report"
echo "  python3 cli.py batch --input addresses.csv --output results.xlsx --format excel --report report.txt"
echo ""
echo "For more information, see README.md"
