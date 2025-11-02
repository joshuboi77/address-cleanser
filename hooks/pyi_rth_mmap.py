# PyInstaller runtime hook to ensure mmap and cmath modules are available
# This is loaded before the main script to ensure these modules are imported early
import sys

# Force import of mmap to ensure it's bundled
try:
    import mmap
except ImportError:
    import warnings
    warnings.warn("mmap module not available")

# Force import of cmath to ensure it's bundled  
try:
    import cmath
except ImportError:
    import warnings
    warnings.warn("cmath module not available")

