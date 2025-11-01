#!/usr/bin/env python3
"""
Build executable for address-cleanser using PyInstaller.
Enhanced for macOS distribution with Universal2 support and proper naming.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def build_executable():
    """Build executable for current platform."""
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Check if PyInstaller is available (either as module or via pipx)
    pyinstaller_cmd = "pyinstaller"
    try:
        import PyInstaller
        print("PyInstaller module found")
    except ImportError:
        # Try using pipx-installed pyinstaller
        try:
            subprocess.check_call(["which", "pyinstaller"], stdout=subprocess.DEVNULL)
            print("PyInstaller found via pipx")
        except subprocess.CalledProcessError:
            print("PyInstaller not found. Please install with: pipx install pyinstaller")
            sys.exit(1)
    
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    # Build command
    build_cmd = [
        "pyinstaller",
        "--clean",
        "--onefile",
        "--name", "address-cleanser",
        "--add-data", "out/sample_input.csv:out",
        "--add-data", "README.md:.",
        "--add-data", "LICENSE:.",
        "--additional-hooks-dir", "hooks",
        "--hidden-import", "usaddress",
        "--hidden-import", "pandas",
        "--hidden-import", "openpyxl",
        "--hidden-import", "click",
        "--hidden-import", "tqdm",
        "--hidden-import", "psutil",
        "--hidden-import", "mmap",
        "--collect-all", "usaddress",
        "--collect-all", "pandas",
        "cli.py"
    ]
    
    # Add icon based on platform (only if icon exists)
    icon_path = None
    if system == "windows":
        icon_path = "assets/icon.ico"
    elif system == "darwin":  # macOS
        icon_path = "assets/icon.icns"
    
    if icon_path and Path(icon_path).exists():
        build_cmd.extend(["--icon", icon_path])
    
    print(f"Building executable for {system}-{arch}...")
    print(f"Command: {' '.join(build_cmd)}")
    
    try:
        subprocess.check_call(build_cmd)
        print("Build successful!")
        
        # Handle executable naming and placement
        exe_name = "address-cleanser"
        if system == "windows":
            exe_name += ".exe"
        
        source = Path("dist") / exe_name
        
        # Create properly named target
        if system == "darwin":
            # For macOS, create both arch-specific and universal names
            target_arch = Path("dist") / f"address-cleanser-darwin-{arch}"
            target_universal = Path("dist") / "address-cleanser-darwin-universal"
            
            if source.exists():
                # Copy to arch-specific name
                shutil.copy2(source, target_arch)
                print(f"Arch-specific executable created: {target_arch}")
                
                # For Universal2 builds, we'll handle this in the GitHub Actions
                # For now, just create a symlink to the arch-specific version
                if target_universal.exists():
                    target_universal.unlink()
                target_universal.symlink_to(target_arch.name)
                print(f"Universal executable created: {target_universal}")
        else:
            # For other platforms, use the original naming
            target = Path("dist") / f"address-cleanser-{system}-{arch}"
            if system == "windows":
                target = target.with_suffix(".exe")
            
            if source.exists():
                source.rename(target)
                print(f"Executable created: {target}")
            else:
                print(f"Executable not found: {source}")
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)

def create_universal_binary():
    """Create Universal2 binary for macOS (Intel + Apple Silicon)."""
    if platform.system().lower() != "darwin":
        print("Universal2 builds are only supported on macOS")
        return False
    
    try:
        # Check if we have both architectures built
        arm64_path = Path("dist") / "address-cleanser-darwin-arm64"
        x86_64_path = Path("dist") / "address-cleanser-darwin-x86_64"
        
        if not arm64_path.exists() or not x86_64_path.exists():
            print("Both ARM64 and x86_64 builds are required for Universal2")
            return False
        
        # Create Universal2 binary using lipo
        universal_path = Path("dist") / "address-cleanser-darwin-universal"
        subprocess.check_call([
            "lipo", "-create", "-output", str(universal_path),
            str(arm64_path), str(x86_64_path)
        ])
        
        print(f"Universal2 binary created: {universal_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to create Universal2 binary: {e}")
        return False

if __name__ == "__main__":
    build_executable()
