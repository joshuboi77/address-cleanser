# PyInstaller hook for mmap module
# Ensures mmap extension module is included in the executable

# mmap is a built-in C extension module that pandas uses internally
hiddenimports = ['mmap', '_mmap']

