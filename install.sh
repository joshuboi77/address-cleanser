#!/bin/bash
# Address Cleanser Installer
# One-line installation script for macOS and Linux

set -e

REPO="joshuboi77/address-cleanser"
INSTALL_DIR="$HOME/.local/bin"

echo "🔧 Installing Address Cleanser..."

# Detect platform
OS=$(uname -s)
ARCH=$(uname -m)

echo "📱 Detected platform: $OS $ARCH"

# Determine binary name and download URL
if [[ "$OS" == "Darwin" ]]; then
    BINARY_NAME="address-cleanser-darwin-universal"
    PLATFORM="macos"
elif [[ "$OS" == "Linux" ]]; then
    if [[ "$ARCH" == "x86_64" ]]; then
        BINARY_NAME="address-cleanser-linux-x86_64"
    elif [[ "$ARCH" == "aarch64" ]]; then
        BINARY_NAME="address-cleanser-linux-aarch64"
    else
        echo "❌ Unsupported Linux architecture: $ARCH"
        echo "Supported architectures: x86_64, aarch64"
        exit 1
    fi
    PLATFORM="linux"
else
    echo "❌ Unsupported operating system: $OS"
    echo "Supported systems: macOS (Darwin), Linux"
    exit 1
fi

# Get latest release
echo "🔍 Fetching latest release information..."
LATEST_RELEASE=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | grep -o '"tag_name": "[^"]*' | cut -d'"' -f4)

if [[ -z "$LATEST_RELEASE" ]]; then
    echo "❌ Failed to fetch latest release information"
    exit 1
fi

echo "📦 Latest release: $LATEST_RELEASE"

# Download URL
DOWNLOAD_URL="https://github.com/$REPO/releases/download/$LATEST_RELEASE/$BINARY_NAME.zip"
echo "⬇️  Downloading from: $DOWNLOAD_URL"

# Create install directory
mkdir -p "$INSTALL_DIR"

# Download and extract
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

echo "📥 Downloading binary..."
if ! curl -L "$DOWNLOAD_URL" -o "$BINARY_NAME.zip"; then
    echo "❌ Failed to download binary"
    exit 1
fi

echo "📦 Extracting binary..."
if ! unzip -q "$BINARY_NAME.zip"; then
    echo "❌ Failed to extract binary"
    exit 1
fi

# Verify binary exists
if [[ ! -f "$BINARY_NAME" ]]; then
    echo "❌ Binary not found after extraction: $BINARY_NAME"
    exit 1
fi

# Install binary
echo "🔧 Installing binary to $INSTALL_DIR..."
mv "$BINARY_NAME" "$INSTALL_DIR/address-cleanser"
chmod +x "$INSTALL_DIR/address-cleanser"

# Clean up
cd /
rm -rf "$TEMP_DIR"

# Add to PATH if not already there
SHELL_RC=""
if [[ "$SHELL" == *"zsh"* ]] || [[ -n "$ZSH_VERSION" ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]] || [[ -n "$BASH_VERSION" ]]; then
    SHELL_RC="$HOME/.bashrc"
else
    # Try to detect shell
    if [[ -f "$HOME/.zshrc" ]]; then
        SHELL_RC="$HOME/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        SHELL_RC="$HOME/.bashrc"
    elif [[ -f "$HOME/.profile" ]]; then
        SHELL_RC="$HOME/.profile"
    fi
fi

if [[ -n "$SHELL_RC" ]] && ! grep -q "$INSTALL_DIR" "$SHELL_RC" 2>/dev/null; then
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$SHELL_RC"
    echo "⚠️  Added $INSTALL_DIR to PATH in $SHELL_RC"
    echo "⚠️  Please restart your terminal or run: source $SHELL_RC"
fi

# Verify installation
if "$INSTALL_DIR/address-cleanser" --help >/dev/null 2>&1; then
    echo "✅ Address Cleanser installed successfully!"
    echo "📍 Location: $INSTALL_DIR/address-cleanser"
    echo "🚀 Run: address-cleanser --help"
    echo ""
    echo "📋 Quick start:"
    echo "  address-cleanser single --single \"123 Main St, Austin, TX 78701\""
    echo "  address-cleanser batch --input addresses.csv --output cleaned.csv"
else
    echo "❌ Installation verification failed"
    echo "The binary was installed but may not be working correctly"
    exit 1
fi