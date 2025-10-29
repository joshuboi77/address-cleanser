#!/bin/bash
# Clean distribution script for Address Cleanser
# Creates ZIP + PKG + Homebrew formula with canonical naming

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
BINARY_PATH="$PROJECT_ROOT/dist/address-cleanser"
OUTPUT_DIR="$PROJECT_ROOT/dist/release"
VERSION="${1:-1.0.7}"
ARCH="${2:-arm64}"

echo "Creating distribution for version $VERSION (arch: $ARCH)..."

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check if binary exists
if [[ ! -f "$BINARY_PATH" ]]; then
    echo "Binary not found at $BINARY_PATH"
    echo "Please run packaging/build.sh first"
    exit 1
fi

# 1. Codesign the binary (if credentials available)
echo "Codesigning binary..."
if [[ -n "${DEVELOPER_ID:-}" ]]; then
    codesign --force --sign "$DEVELOPER_ID" \
        --options runtime --timestamp "$BINARY_PATH"
    echo "✅ Binary codesigned"
else
    echo "⚠️  Skipping codesigning (DEVELOPER_ID not set)"
fi

# 2. Create ZIP archive
echo "Creating ZIP archive..."
ZIP_NAME="address-cleanser-macos-${ARCH}.zip"
ZIP_PATH="$OUTPUT_DIR/$ZIP_NAME"

(cd "$PROJECT_ROOT/dist" && zip -r "$ZIP_PATH" address-cleanser)
echo "✅ Created ZIP: $ZIP_PATH"

# 3. Notarize ZIP (if credentials available)
if [[ -n "${APPLE_ID:-}" && -n "${TEAM_ID:-}" && -n "${APP_PASSWORD:-}" ]]; then
    echo "Notarizing ZIP..."
    xcrun notarytool submit "$ZIP_PATH" \
        --apple-id "$APPLE_ID" \
        --team-id "$TEAM_ID" \
        --password "$APP_PASSWORD" \
        --wait
    
    echo "Stapling notarization ticket..."
    xcrun stapler staple "$ZIP_PATH"
    echo "✅ ZIP notarized and stapled"
else
    echo "⚠️  Skipping notarization (credentials not set)"
fi

# 4. Create per-user PKG installer
echo "Creating per-user PKG installer..."
PKG_NAME="address-cleanser-user.pkg"
PKG_PATH="$OUTPUT_DIR/$PKG_NAME"

# Create temporary directory for PKG structure
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Create package structure
mkdir -p "$TEMP_DIR/Scripts"
mkdir -p "$TEMP_DIR/Resources"

# Copy binary to Resources
cp "$BINARY_PATH" "$TEMP_DIR/Resources/address-cleanser"

# Copy postinstall script
cp "$SCRIPT_DIR/pkg/Scripts/postinstall" "$TEMP_DIR/Scripts/postinstall"
chmod 755 "$TEMP_DIR/Scripts/postinstall"

# Create component package (no root, just scripts)
pkgbuild \
    --identifier "com.address-cleanser" \
    --version "$VERSION" \
    --install-location "/" \
    --scripts "$TEMP_DIR/Scripts" \
    "$TEMP_DIR/address-cleanser.pkg"

# Create distribution package
productbuild \
    --distribution "$SCRIPT_DIR/pkg/distribution-user.xml" \
    --package-path "$TEMP_DIR" \
    --resources "$TEMP_DIR/Resources" \
    --identifier "com.address-cleanser.dist" \
    --version "$VERSION" \
    "$PKG_PATH"

echo "✅ Created PKG: $PKG_PATH"

# 5. Sign PKG (if credentials available)
if [[ -n "${DEVELOPER_ID_INSTALLER:-}" ]]; then
    echo "Signing PKG..."
    productsign --sign "$DEVELOPER_ID_INSTALLER" \
        "$PKG_PATH" "${PKG_PATH}.signed"
    mv "${PKG_PATH}.signed" "$PKG_PATH"
    echo "✅ PKG signed"
else
    echo "⚠️  Skipping PKG signing (DEVELOPER_ID_INSTALLER not set)"
fi

# 6. Notarize PKG (if credentials available)
if [[ -n "${APPLE_ID:-}" && -n "${TEAM_ID:-}" && -n "${APP_PASSWORD:-}" ]]; then
    echo "Notarizing PKG..."
    xcrun notarytool submit "$PKG_PATH" \
        --apple-id "$APPLE_ID" \
        --team-id "$TEAM_ID" \
        --password "$APP_PASSWORD" \
        --wait
    
    echo "Stapling notarization ticket..."
    xcrun stapler staple "$PKG_PATH"
    echo "✅ PKG notarized and stapled"
else
    echo "⚠️  Skipping PKG notarization (credentials not set)"
fi

# 7. Generate checksums
echo "Generating checksums..."
CHECKSUMS_PATH="$OUTPUT_DIR/checksums.txt"
shasum -a 256 "$ZIP_PATH" "$PKG_PATH" > "$CHECKSUMS_PATH"
echo "✅ Created checksums: $CHECKSUMS_PATH"

# 8. Generate Homebrew formula
echo "Generating Homebrew formula..."
FORMULA_PATH="$OUTPUT_DIR/address-cleanser.rb"

# Get ZIP checksum
ZIP_CHECKSUM=$(shasum -a 256 "$ZIP_PATH" | cut -d' ' -f1)

# Generate formula from template
sed -e "s/{{VERSION}}/$VERSION/g" \
    -e "s/{{SHA256_ARM64}}/$ZIP_CHECKSUM/g" \
    -e "s/{{SHA256_X64}}/PLACEHOLDER/g" \
    "$SCRIPT_DIR/brew/address-cleanser.rb.tmpl" > "$FORMULA_PATH"

echo "✅ Created Homebrew formula: $FORMULA_PATH"

# 9. Copy install script
echo "Copying install script..."
cp "$SCRIPT_DIR/install.sh" "$OUTPUT_DIR/install.sh"
echo "✅ Copied install script"

echo ""
echo "🎉 Distribution complete!"
echo "Files created in $OUTPUT_DIR:"
ls -la "$OUTPUT_DIR"
