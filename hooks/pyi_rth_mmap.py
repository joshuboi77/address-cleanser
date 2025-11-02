# PyInstaller runtime hook to ensure mmap module is available
# This is loaded before the main script to ensure mmap is imported early
import sys

# Force import of mmap to ensure it's bundled
# mmap uses _mmap internally (C extension)
try:
    import mmap
    # Verify mmap is working
    if hasattr(mmap, 'PAGESIZE'):
        # mmap is loaded correctly
        pass
except ImportError:
    # This should not happen if mmap is bundled correctly
    import warnings
    warnings.warn("mmap module not available - may cause issues with pandas")

