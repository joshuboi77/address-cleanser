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
for module_name in ['pandas.testing', 'pandas._testing', 'pandas.tests']:
    create_dummy_module(module_name)

# Also patch __import__ to catch any late imports
_original_import = __import__

def patched_import(name, globals=None, locals=None, fromlist=(), level=0):
    """Patch __import__ to skip pandas testing modules."""
    if name in ('pandas.testing', 'pandas._testing', 'pandas.tests'):
        return create_dummy_module(name)
    return _original_import(name, globals, locals, fromlist, level)

# Replace builtins.__import__ with our patched version
import builtins
builtins.__import__ = patched_import
