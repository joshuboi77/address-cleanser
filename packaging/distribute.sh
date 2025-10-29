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

# 4. Generate checksums
echo "Generating checksums..."
CHECKSUMS_PATH="$OUTPUT_DIR/checksums.txt"
shasum -a 256 "$ZIP_PATH" > "$CHECKSUMS_PATH"
echo "✅ Created checksums: $CHECKSUMS_PATH"

# 5. Generate Homebrew formula
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

# 6. Copy install script
echo "Copying install script..."
cp "$SCRIPT_DIR/install.sh" "$OUTPUT_DIR/install.sh"
echo "✅ Copied install script"

echo ""
echo "🎉 Distribution complete!"
echo "Files created in $OUTPUT_DIR:"
ls -la "$OUTPUT_DIR"
