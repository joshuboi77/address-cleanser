# PyInstaller runtime hook to ensure cmath module is available
import sys

# Force import of cmath to ensure it's bundled
try:
    import cmath
except ImportError:
    import warnings
    warnings.warn("cmath module not available")

