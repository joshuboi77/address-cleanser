# PyInstaller hook for mmap module
# Ensures mmap extension module is included in the executable

# mmap is a built-in extension module, so we just need to ensure it's recognized
hiddenimports = ['mmap']

