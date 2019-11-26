# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['vintel.py', 'vi/esi/esiinterface.py', 'vi/cache/cache.py', 'vi/character/Characters.py', 'vi/chatparser/chatparser.py',
 'vi/jumpbridge/Import.py', 'vi/region/RegionMenu.py', 'vi/sound/soundmanager.py'],
             pathex=['D:\\Develop\\vintel\\src'],
             binaries=[],
             datas=[(HOMEPATH + '\\PyQt5\\Qt\\bin\*', 'PyQt5\\Qt\\bin'), ('vi/ui/res/logo.png', 'img/logo.png')],
             hiddenimports=[],
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
          [],
          exclude_binaries=True,
          name='vintel',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='vintel')
