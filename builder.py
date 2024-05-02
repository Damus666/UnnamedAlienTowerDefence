import PyInstaller.__main__

PyInstaller.__main__.run([
    'EvergreenDefense.py',
    '--onefile',
    '--windowed',
])

PyInstaller.__main__.run([
    'EvergreenDefenseMapEditor.py',
    '--onefile',
    '--windowed',
])