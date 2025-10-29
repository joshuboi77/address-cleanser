#!/bin/bash
# Local testing script for macOS distribution
# This script helps test the distribution process locally

set -e

echo "🧪 Testing macOS Distribution Process"

# Check if we're on macOS
if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "❌ This script is for macOS only"
    exit 1
fi

# Check for required tools
echo "🔍 Checking required tools..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required"
    exit 1
fi

if ! command -v codesign &> /dev/null; then
    echo "❌ codesign is required (part of Xcode Command Line Tools)"
    exit 1
fi

if ! command -v xcrun &> /dev/null; then
    echo "❌ xcrun is required (part of Xcode Command Line Tools)"
    exit 1
fi

echo "✅ All required tools found"

# Build the executable
echo "🔨 Building executable..."
python3 scripts/build_executable.py

# Check if binary was created
BINARY_PATH="dist/address-cleanser-darwin-$(uname -m)"
if [[ ! -f "$BINARY_PATH" ]]; then
    echo "❌ Binary not found: $BINARY_PATH"
    exit 1
fi

echo "✅ Binary created: $BINARY_PATH"

# Test the binary
echo "🧪 Testing binary..."
if "$BINARY_PATH" --help >/dev/null 2>&1; then
    echo "✅ Binary works correctly"
else
    echo "❌ Binary test failed"
    exit 1
fi

# Test distribution script (without credentials)
echo "📦 Testing distribution script..."
if python3 scripts/macos_distribution.py "$BINARY_PATH" --output-dir dist/test-distribution --version "1.0.0-test"; then
    echo "✅ Distribution script completed"
    
    # List created files
    echo "📁 Created distribution files:"
    ls -la dist/test-distribution/
else
    echo "❌ Distribution script failed"
    exit 1
fi

# Test installer script
echo "🔧 Testing installer script..."
if bash -n install.sh; then
    echo "✅ Installer script syntax is valid"
else
    echo "❌ Installer script has syntax errors"
    exit 1
fi

# Test Homebrew formula
echo "🍺 Testing Homebrew formula..."
if ruby -c homebrew/Formula/address-cleanser.rb; then
    echo "✅ Homebrew formula syntax is valid"
else
    echo "❌ Homebrew formula has syntax errors"
    exit 1
fi

echo ""
echo "🎉 All tests passed!"
echo ""
echo "📋 Next steps for full distribution:"
echo "1. Set up Apple Developer credentials:"
echo "   - Developer ID Application certificate"
echo "   - Apple ID and app-specific password"
echo "   - Team ID"
echo ""
echo "2. Add GitHub secrets:"
echo "   - DEVELOPER_ID"
echo "   - APPLE_ID"
echo "   - TEAM_ID"
echo "   - APP_PASSWORD"
echo ""
echo "3. Create a release tag:"
echo "   git tag v1.0.0"
echo "   git push origin v1.0.0"
echo ""
echo "4. GitHub Actions will automatically:"
echo "   - Build Universal2 binary"
echo "   - Codesign and notarize packages"
echo "   - Create all distribution files"
echo "   - Upload to GitHub Releases"
