# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(['src\\main.py'],
             pathex=['.\\'],
             binaries=[],
             datas=[
                 ('src', 'src'),
                 ('icons', 'icons'),
                 ('Config', 'Config'),
                 ('logs', 'logs')
             ],
             hiddenimports=['PyQt5', 'pywin32', 'psutil', 'loguru'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='BetterExplorer',
          debug=False,
          bootloader_ignore_signals=False,
          console=False,
          strip=True,
          upx=True,
          upx_exclude=[],
          runtime_info_entries=None,
          disable_windowed_traceback=False,
          argv_emulation=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )