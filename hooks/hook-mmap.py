# PyInstaller hook for mmap module
# Ensures mmap extension module is included in the executable

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect mmap as a hidden import
hiddenimports = ['mmap']

# Also collect any mmap-related modules
datas, binaries, hiddenimports = collect_all('mmap', include_py_data=True)

