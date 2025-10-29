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
    
    # Add icon based on platform (only if icon exists)
    system = platform.system().lower()
    icon_path = None
    if system == "windows":
        icon_path = "assets/icon.ico"
    elif system == "darwin":  # macOS
        icon_path = "assets/icon.icns"
    
    if icon_path and Path(icon_path).exists():
        build_cmd.extend(["--icon", icon_path])
    
    print(f"Building executable for {system}...")
    print(f"Command: {' '.join(build_cmd)}")
    
    try:
        subprocess.check_call(build_cmd)
        print("Build successful!")
        
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
            print(f"Executable created: {target}")
        else:
            print(f"Executable not found: {source}")
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()
