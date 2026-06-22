# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

from PyInstaller.utils.hooks import collect_data_files
import cv2

mediapipe_datas = collect_data_files('mediapipe')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/*.tflite', 'assets'),
        ('assets/*.onnx', 'assets'),
        (cv2.data.haarcascades, 'cv2/data'),
    ] + mediapipe_datas,
    hiddenimports=[
        'pytesseract', 'cv2', 'numpy', 'fitz', 'PIL', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
        'qdarktheme', 'mediapipe'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'fonttools', 'sounddevice', 'setuptools', 'distutils',
        'scipy', 'pandas', 'IPython', 'notebook'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SafeMARC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
