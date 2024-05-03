import PyInstaller.__main__
import os
import shutil

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

print("\n")

os.remove("EvergreenDefense.spec")
os.remove("EvergreenDefenseMapEditor.spec")
shutil.rmtree("build")
shutil.copytree("assets", "dist/assets")

print(f"EvergreenDefense.exe created in dist/")
print(f"EvergreenDefenseMapEditor.exe created in dist/")
print(f"Deleted build/, EvergreenDefense.spec, EvergreenDefenseMapEditor.spec")
print(f"Copied assets/ to dist/assets")
