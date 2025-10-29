# Cross-Platform Executable Build Configuration

## Overview

This configuration creates standalone executables for Windows, macOS, and Linux using PyInstaller, automatically built via GitHub Actions and released on GitHub.

## PyInstaller Configuration

### 1. Create PyInstaller Spec File

```python
# build/address-cleanser.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('out/sample_input.csv', 'out'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'usaddress',
        'pandas',
        'openpyxl',
        'click',
        'tqdm',
        'psutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='address-cleanser',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.name == 'nt' else 'assets/icon.icns',
)
```

### 2. Build Script

```python
# scripts/build_executable.py
#!/usr/bin/env python3
"""
Build executable for address-cleanser using PyInstaller.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def build_executable():
    """Build executable for current platform."""
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Install PyInstaller if not already installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build command
    build_cmd = [
        "pyinstaller",
        "--clean",
        "--onefile",
        "--name", "address-cleanser",
        "--add-data", "out/sample_input.csv:out",
        "--add-data", "README.md:.",
        "--add-data", "LICENSE:.",
        "--hidden-import", "usaddress",
        "--hidden-import", "pandas",
        "--hidden-import", "openpyxl",
        "--hidden-import", "click",
        "--hidden-import", "tqdm",
        "--hidden-import", "psutil",
        "cli.py"
    ]
    
    # Add icon based on platform
    system = platform.system().lower()
    if system == "windows":
        build_cmd.extend(["--icon", "assets/icon.ico"])
    elif system == "darwin":  # macOS
        build_cmd.extend(["--icon", "assets/icon.icns"])
    
    print(f"Building executable for {system}...")
    print(f"Command: {' '.join(build_cmd)}")
    
    try:
        subprocess.check_call(build_cmd)
        print("✅ Build successful!")
        
        # Move executable to dist folder with platform suffix
        exe_name = "address-cleanser"
        if system == "windows":
            exe_name += ".exe"
        
        source = Path("dist") / exe_name
        target = Path("dist") / f"address-cleanser-{system}-{platform.machine()}"
        if system == "windows":
            target = target.with_suffix(".exe")
        
        if source.exists():
            source.rename(target)
            print(f"✅ Executable created: {target}")
        else:
            print(f"❌ Executable not found: {source}")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()
```

### 3. GitHub Actions Workflow

```yaml
# .github/workflows/build-release.yml
name: Build and Release

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.11']
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build executable
      run: |
        python scripts/build_executable.py
    
    - name: Upload artifacts
      uses: actions/upload-artifact@v3
      with:
        name: address-cleanser-${{ matrix.os }}
        path: dist/
    
    - name: Create checksums
      if: matrix.os == 'ubuntu-latest'
      run: |
        cd dist
        sha256sum * > checksums.txt
    
    - name: Upload checksums
      if: matrix.os == 'ubuntu-latest'
      uses: actions/upload-artifact@v3
      with:
        name: checksums
        path: dist/checksums.txt

  release:
    needs: build
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Download all artifacts
      uses: actions/download-artifact@v3
    
    - name: Prepare release assets
      run: |
        mkdir -p release-assets
        
        # Copy executables from each platform
        cp address-cleanser-ubuntu-latest/* release-assets/ 2>/dev/null || true
        cp address-cleanser-windows-latest/* release-assets/ 2>/dev/null || true
        cp address-cleanser-macos-latest/* release-assets/ 2>/dev/null || true
        cp checksums/checksums.txt release-assets/ 2>/dev/null || true
        
        # Create archive with all executables
        cd release-assets
        tar -czf address-cleanser-all-platforms.tar.gz *
        zip -r address-cleanser-all-platforms.zip *
    
    - name: Create Release
      uses: softprops/action-gh-release@v1
      with:
        files: |
          release-assets/*
        body: |
          ## Address Cleanser ${{ github.ref_name }}
          
          ### Downloads
          
          **All Platforms Archive:**
          - `address-cleanser-all-platforms.tar.gz` (Linux/macOS)
          - `address-cleanser-all-platforms.zip` (Windows)
          
          **Individual Executables:**
          - `address-cleanser-linux-*` - Linux executable
          - `address-cleanser-windows-*.exe` - Windows executable  
          - `address-cleanser-darwin-*` - macOS executable
          
          ### Installation
          
          1. Download the appropriate executable for your platform
          2. Make it executable (Linux/macOS): `chmod +x address-cleanser-linux-*`
          3. Run: `./address-cleanser-linux-* --help`
          
          ### Verification
          
          Verify file integrity using the provided checksums:
          ```bash
          sha256sum -c checksums.txt
          ```
          
          ### Usage Examples
          
          ```bash
          # Process a single address
          ./address-cleanser-linux-* single --single "123 Main St, Austin, TX 78701"
          
          # Process a CSV file
          ./address-cleanser-linux-* batch --input addresses.csv --output cleaned.csv
          ```
        draft: false
        prerelease: false
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 4. Local Build Script

```bash
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
```

### 5. Requirements for Build

```txt
# requirements-build.txt
pyinstaller>=5.13.0
usaddress>=0.5.10
pandas>=2.0.0
openpyxl>=3.1.5
click>=8.1.8
tqdm>=4.66.1
psutil>=6.1.1
```

### 6. Icon Assets (Optional)

Create icon files for better branding:

```bash
# Create assets directory
mkdir -p assets

# You can create icons using online tools or design software
# - assets/icon.ico (Windows, 256x256)
# - assets/icon.icns (macOS, 512x512)
# - assets/icon.png (Linux, 256x256)
```

### 7. Usage Instructions

```markdown
# EXECUTABLE_USAGE.md

## Download and Installation

1. **Download**: Go to [Releases](https://github.com/joshuboi77/address-cleanser/releases)
2. **Choose Platform**: Download the appropriate executable for your OS
3. **Make Executable** (Linux/macOS):
   ```bash
   chmod +x address-cleanser-linux-*
   ```
4. **Run**: 
   ```bash
   ./address-cleanser-linux-* --help
   ```

## Platform-Specific Notes

### Windows
- Download `address-cleanser-windows-*.exe`
- Run from Command Prompt or PowerShell
- May need to allow execution in Windows Defender

### macOS
- Download `address-cleanser-darwin-*`
- May need to allow execution in Security & Privacy settings
- Run from Terminal

### Linux
- Download `address-cleanser-linux-*`
- Make executable: `chmod +x address-cleanser-linux-*`
- Run from terminal

## Verification

Check file integrity using provided checksums:
```bash
sha256sum -c checksums.txt
```

## Examples

```bash
# Single address processing
./address-cleanser-linux-* single --single "123 Main St, Austin, TX 78701"

# Batch processing
./address-cleanser-linux-* batch --input addresses.csv --output cleaned.csv --format csv

# With validation report
./address-cleanser-linux-* batch --input addresses.csv --output cleaned.csv --report validation.txt
```
```

## Quick Setup Commands

```bash
# 1. Create the build script
mkdir -p scripts build assets

# 2. Make build script executable
chmod +x scripts/build_local.sh

# 3. Install PyInstaller
pip install pyinstaller

# 4. Build locally
./scripts/build_local.sh

# 5. Test the executable
./dist/address-cleanser-linux-* --help
```

## Release Process

1. **Create a tag**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. **GitHub Actions will automatically**:
   - Build executables for all platforms
   - Create a GitHub release
   - Upload all executables and checksums

3. **Users can download** from the GitHub releases page

This setup gives you professional, cross-platform executables that users can download and run without installing Python or dependencies!
