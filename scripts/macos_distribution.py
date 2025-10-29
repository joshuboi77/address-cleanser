#!/usr/bin/env python3
"""
macOS Distribution Script for Address Cleanser

This script handles:
1. Codesigning with Developer ID
2. Notarization via Apple
3. Creating distribution packages (ZIP, PKG, Homebrew)
4. Staple notarization tickets
"""

import os
import sys
import subprocess
import shutil
import zipfile
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

class MacOSDistributor:
    def __init__(self, 
                 developer_id: Optional[str] = None,
                 apple_id: Optional[str] = None,
                 team_id: Optional[str] = None,
                 app_password: Optional[str] = None):
        """
        Initialize the macOS distributor.
        
        Args:
            developer_id: Developer ID Application certificate name
            apple_id: Apple ID for notarization
            team_id: Apple Developer Team ID
            app_password: App-specific password for notarization
        """
        self.developer_id = developer_id or os.getenv('DEVELOPER_ID')
        self.apple_id = apple_id or os.getenv('APPLE_ID')
        self.team_id = team_id or os.getenv('TEAM_ID')
        self.app_password = app_password or os.getenv('APP_PASSWORD')
        
        # Validate required credentials
        if not all([self.developer_id, self.apple_id, self.team_id, self.app_password]):
            print("Warning: Not all credentials provided. Some features will be disabled.")
            print("Required environment variables:")
            print("  DEVELOPER_ID: Developer ID Application certificate name")
            print("  APPLE_ID: Apple ID for notarization")
            print("  TEAM_ID: Apple Developer Team ID")
            print("  APP_PASSWORD: App-specific password for notarization")

    def codesign_binary(self, binary_path: Path) -> bool:
        """Codesign a binary with Developer ID."""
        if not self.developer_id:
            print("Skipping codesigning: DEVELOPER_ID not provided")
            return False
            
        try:
            print(f"Codesigning {binary_path}...")
            subprocess.check_call([
                "codesign",
                "--sign", self.developer_id,
                "--options", "runtime",
                "--timestamp",
                "--force",
                str(binary_path)
            ])
            print(f"✅ Codesigned: {binary_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Codesigning failed: {e}")
            return False

    def notarize_archive(self, archive_path: Path) -> bool:
        """Notarize an archive via Apple."""
        if not all([self.apple_id, self.team_id, self.app_password]):
            print("Skipping notarization: Required credentials not provided")
            return False
            
        try:
            print(f"Notarizing {archive_path}...")
            
            # Submit for notarization
            result = subprocess.run([
                "xcrun", "notarytool", "submit", str(archive_path),
                "--apple-id", self.apple_id,
                "--team-id", self.team_id,
                "--password", self.app_password,
                "--wait"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Notarization failed: {result.stderr}")
                return False
                
            print(f"✅ Notarized: {archive_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Notarization failed: {e}")
            return False

    def staple_ticket(self, archive_path: Path) -> bool:
        """Staple notarization ticket to archive."""
        try:
            print(f"Stapling ticket to {archive_path}...")
            subprocess.check_call([
                "xcrun", "stapler", "staple", str(archive_path)
            ])
            print(f"✅ Stapled: {archive_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Stapling failed: {e}")
            return False

    def create_zip_archive(self, binary_path: Path, output_dir: Path) -> Path:
        """Create a ZIP archive for distribution."""
        archive_name = f"{binary_path.stem}.zip"
        archive_path = output_dir / archive_name
        
        print(f"Creating ZIP archive: {archive_path}")
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(binary_path, binary_path.name)
            
        print(f"✅ Created ZIP: {archive_path}")
        return archive_path

    def create_pkg_installer(self, binary_path: Path, output_dir: Path) -> Optional[Path]:
        """Create a PKG installer for GUI-friendly installation."""
        try:
            pkg_name = f"{binary_path.stem}.pkg"
            pkg_path = output_dir / pkg_name
            
            # Create a temporary directory for the package structure
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create package structure for user installation
                # Install to Applications folder to avoid system volume issues
                apps_dir = temp_path / "Applications" / "Address Cleanser"
                apps_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy binary and rename it
                installed_binary = apps_dir / "address-cleanser"
                shutil.copy2(binary_path, installed_binary)
                
                # Create distribution XML for better compatibility
                distribution_xml = temp_path / "distribution.xml"
                with open(distribution_xml, 'w') as f:
                    f.write('''<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>Address Cleanser</title>
    <organization>com.address-cleanser</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="false"/>
    <choices-outline>
        <line choice="default">
            <line choice="com.address-cleanser.cli"/>
        </line>
    </choices-outline>
    <choice id="default"/>
    <choice id="com.address-cleanser.cli" visible="false">
        <pkg-ref id="com.address-cleanser.cli"/>
    </choice>
    <pkg-ref id="com.address-cleanser.cli" version="1.0.0" onConclusion="none">component.pkg</pkg-ref>
</installer-gui-script>''')
                
                # Create component package
                component_pkg = temp_path / "component.pkg"
                subprocess.check_call([
                    "pkgbuild",
                    "--root", str(temp_path),
                    "--identifier", "com.address-cleanser.cli",
                    "--version", "1.0.0",
                    "--install-location", "/",
                    str(component_pkg)
                ])
                
                # Create distribution package
                subprocess.check_call([
                    "productbuild",
                    "--distribution", str(distribution_xml),
                    "--package-path", str(temp_path),
                    str(pkg_path)
                ])
                
            print(f"✅ Created PKG: {pkg_path}")
            return pkg_path
            
        except subprocess.CalledProcessError as e:
            print(f"❌ PKG creation failed: {e}")
            return None

    def create_homebrew_formula(self, binary_path: Path, output_dir: Path, 
                              version: str = "1.0.0", 
                              github_repo: str = "joshuboi77/address-cleanser") -> Path:
        """Create a Homebrew formula for easy installation."""
        formula_name = "address-cleanser.rb"
        formula_path = output_dir / formula_name
        
        # Calculate SHA256 checksum
        import hashlib
        with open(binary_path, 'rb') as f:
            sha256_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Get file size
        file_size = binary_path.stat().st_size
        
        formula_content = f'''class AddressCleanser < Formula
  desc "Parse, validate, and format US addresses"
  homepage "https://github.com/{github_repo}"
  url "https://github.com/{github_repo}/releases/download/v{version}/address-cleanser-darwin-universal.zip"
  sha256 "{sha256_hash}"
  version "{version}"
  license "MIT"

  def install
    bin.install "address-cleanser-darwin-universal" => "address-cleanser"
  end

  test do
    assert_match "Address Cleanser", shell_output("#{{bin}}/address-cleanser --help")
  end
end
'''
        
        with open(formula_path, 'w') as f:
            f.write(formula_content)
            
        print(f"✅ Created Homebrew formula: {formula_path}")
        return formula_path

    def create_installer_script(self, binary_path: Path, output_dir: Path,
                              github_repo: str = "joshuboi77/address-cleanser") -> Path:
        """Create a one-line installer script."""
        script_name = "install.sh"
        script_path = output_dir / script_name
        
        script_content = f'''#!/bin/bash
# Address Cleanser Installer
# One-line installation script

set -e

REPO="{github_repo}"
BINARY_NAME="address-cleanser-darwin-universal"
INSTALL_DIR="$HOME/.local/bin"

echo "🔧 Installing Address Cleanser..."

# Detect architecture
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    ARCH_SUFFIX="arm64"
elif [[ "$ARCH" == "x86_64" ]]; then
    ARCH_SUFFIX="x86_64"
else
    echo "❌ Unsupported architecture: $ARCH"
    exit 1
fi

# Get latest release
LATEST_RELEASE=$(curl -s "https://api.github.com/repos/$REPO/releases/latest" | grep -o '"tag_name": "[^"]*' | cut -d'"' -f4)
echo "📦 Latest release: $LATEST_RELEASE"

# Download URL
DOWNLOAD_URL="https://github.com/$REPO/releases/download/$LATEST_RELEASE/$BINARY_NAME.zip"
echo "⬇️  Downloading from: $DOWNLOAD_URL"

# Create install directory
mkdir -p "$INSTALL_DIR"

# Download and extract
cd "$(mktemp -d)"
curl -L "$DOWNLOAD_URL" -o "$BINARY_NAME.zip"
unzip "$BINARY_NAME.zip"

# Install binary
mv "$BINARY_NAME" "$INSTALL_DIR/address-cleanser"
chmod +x "$INSTALL_DIR/address-cleanser"

# Add to PATH if not already there
if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo "export PATH=\"$INSTALL_DIR:$PATH\"" >> "$HOME/.bashrc"
    echo "export PATH=\"$INSTALL_DIR:$PATH\"" >> "$HOME/.zshrc"
    echo "⚠️  Added $INSTALL_DIR to PATH in .bashrc and .zshrc"
    echo "⚠️  Please restart your terminal or run: source ~/.bashrc"
fi

echo "✅ Address Cleanser installed successfully!"
echo "📍 Location: $INSTALL_DIR/address-cleanser"
echo "🚀 Run: address-cleanser --help"
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
            
        # Make script executable
        os.chmod(script_path, 0o755)
        
        print(f"✅ Created installer script: {script_path}")
        return script_path

    def distribute_binary(self, binary_path: Path, output_dir: Path, 
                         version: str = "1.0.0") -> Dict[str, Path]:
        """Complete distribution pipeline for a binary."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        # 1. Codesign the binary
        if self.codesign_binary(binary_path):
            results['codesigned'] = binary_path
        
        # 2. Create ZIP archive
        zip_path = self.create_zip_archive(binary_path, output_dir)
        results['zip'] = zip_path
        
        # 3. Notarize ZIP
        if self.notarize_archive(zip_path):
            results['notarized'] = zip_path
            
            # 4. Staple ticket
            if self.staple_ticket(zip_path):
                results['stapled'] = zip_path
        
        # 5. Create PKG installer
        pkg_path = self.create_pkg_installer(binary_path, output_dir)
        if pkg_path:
            results['pkg'] = pkg_path
            
            # Notarize PKG if we have credentials
            if self.notarize_archive(pkg_path):
                self.staple_ticket(pkg_path)
        
        # 6. Create Homebrew formula
        formula_path = self.create_homebrew_formula(binary_path, output_dir, version)
        results['homebrew_formula'] = formula_path
        
        # 7. Create installer script
        script_path = self.create_installer_script(binary_path, output_dir)
        results['installer_script'] = script_path
        
        return results

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="macOS Distribution Script")
    parser.add_argument("binary_path", help="Path to the binary to distribute")
    parser.add_argument("--output-dir", default="dist", help="Output directory")
    parser.add_argument("--version", default="1.0.0", help="Version number")
    parser.add_argument("--developer-id", help="Developer ID certificate name")
    parser.add_argument("--apple-id", help="Apple ID for notarization")
    parser.add_argument("--team-id", help="Apple Developer Team ID")
    parser.add_argument("--app-password", help="App-specific password")
    
    args = parser.parse_args()
    
    binary_path = Path(args.binary_path)
    if not binary_path.exists():
        print(f"❌ Binary not found: {binary_path}")
        sys.exit(1)
    
    distributor = MacOSDistributor(
        developer_id=args.developer_id,
        apple_id=args.apple_id,
        team_id=args.team_id,
        app_password=args.app_password
    )
    
    results = distributor.distribute_binary(
        binary_path, 
        Path(args.output_dir), 
        args.version
    )
    
    print("\n🎉 Distribution complete!")
    print("Created files:")
    for name, path in results.items():
        print(f"  {name}: {path}")

if __name__ == "__main__":
    main()
