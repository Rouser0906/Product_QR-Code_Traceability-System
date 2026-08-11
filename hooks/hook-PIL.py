# Optional hook for Pillow (usually bundled, but safer)
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
hiddenimports = collect_submodules('PIL')
datas = collect_data_files('PIL')
