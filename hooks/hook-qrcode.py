# PyInstaller hook for qrcode
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
hiddenimports = collect_submodules('qrcode')
datas = collect_data_files('qrcode')
