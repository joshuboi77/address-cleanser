# PyInstaller runtime hook to patch pandas initialization
# Prevents pandas from importing testing modules during cleanup
import sys


# Create dummy modules for pandas testing before pandas tries to import them
def create_dummy_module(name):
    """Create a dummy module to prevent ImportError."""
    import types

    if name not in sys.modules:
        dummy = types.ModuleType(name)
        sys.modules[name] = dummy
        # Add minimal attributes to prevent AttributeError
        dummy.__file__ = None
        dummy.__path__ = []
        dummy.__loader__ = None
    return sys.modules[name]


# Pre-create the testing modules that pandas will try to import
# This happens BEFORE pandas.__init__ is loaded
for module_name in ["pandas.testing", "pandas._testing", "pandas.tests"]:
    create_dummy_module(module_name)

# Patch __import__ to catch any late imports and handle cleanup errors gracefully
_original_import = __import__


def patched_import(name, globals=None, locals=None, fromlist=(), level=0):
    """Patch __import__ to skip pandas testing modules and handle cleanup gracefully."""
    # Skip pandas testing modules
    if name in ("pandas.testing", "pandas._testing", "pandas.tests"):
        return create_dummy_module(name)

    # Try normal import first
    try:
        return _original_import(name, globals, locals, fromlist, level)
    except (FileNotFoundError, OSError) as e:
        # Only catch errors related to base_library.zip during cleanup
        # Check if error message mentions the temp directory or base_library.zip
        error_str = str(e)
        if "base_library.zip" in error_str or (
            "_MEI" in error_str and "/base_library.zip" in error_str
        ):
            # We're in cleanup phase and temp directory is gone
            # Create dummy module only for standard library or pandas modules
            if name.startswith("pandas.") or name in ["logging", "zipimport", "importlib"]:
                import types

                dummy = types.ModuleType(name)
                sys.modules[name] = dummy
                dummy.__file__ = None
                return dummy
        # For all other errors (including missing pycrfsuite, etc.), re-raise
        raise


# Replace builtins.__import__ with our patched version
import builtins

builtins.__import__ = patched_import

# Also patch sys.modules.__getitem__ to handle cleanup errors
_original_getitem = sys.modules.__getitem__


def patched_modules_getitem(key):
    """Patch sys.modules.__getitem__ to handle cleanup errors."""
    try:
        return _original_getitem(key)
    except (FileNotFoundError, OSError, KeyError):
        # If we can't access the module due to cleanup, create dummy
        if "_MEI" in str(sys.modules) or "base_library.zip" in str(sys.modules):
            return create_dummy_module(key)
        raise


# Don't patch __getitem__ directly - just catch errors in import
