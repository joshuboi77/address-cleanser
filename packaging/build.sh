#!/bin/bash
# Clean build script for Address Cleanser
# Creates canonical binary name: address-cleanser

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Building Address Cleanser..."

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf "$PROJECT_ROOT/dist" "$PROJECT_ROOT/build"

# Build with PyInstaller
echo "Building with PyInstaller..."
cd "$PROJECT_ROOT"

# Check if PyInstaller is available
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Build the executable
pyinstaller address-cleanser.spec

# Canonicalize name - rename to just 'address-cleanser'
echo "Canonicalizing binary name..."
cd dist
mv address-cleanser* address-cleanser 2>/dev/null || true

# Make executable
chmod +x address-cleanser

echo "Build complete!"
echo "Binary location: $PROJECT_ROOT/dist/address-cleanser"
echo "Binary size: $(du -h address-cleanser | cut -f1)"

# Test the binary
echo "Testing binary..."
if ./address-cleanser --help >/dev/null 2>&1; then
    echo "✅ Binary test passed"
else
    echo "❌ Binary test failed"
    exit 1
fi
