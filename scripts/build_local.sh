#!/bin/bash
# scripts/build_local.sh

set -e

echo "🔨 Building Address Cleanser Executable"

# Check if we're in the right directory
if [ ! -f "cli.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Install PyInstaller if not installed
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create build directory
mkdir -p build dist

# Build executable
echo "🔨 Building executable..."
python scripts/build_executable.py

# Test the executable
echo "🧪 Testing executable..."
if [ -f "dist/address-cleanser" ] || [ -f "dist/address-cleanser.exe" ]; then
    echo "✅ Build successful!"
    echo "📁 Executable location: dist/"
    ls -la dist/
else
    echo "❌ Build failed!"
    exit 1
fi
