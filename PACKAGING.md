"""
Packaging Instructions for Midi Fighter 3D Macro Controller

Requirements
------------
- PyInstaller: pip install pyinstaller
- All project dependencies installed

Quick Start
-----------
1. Build the application:
   pyinstaller MidiFighter3D.spec

2. The packaged app will be in the `dist/MidiFighter3D` folder

3. Test the packaged app:
   ./dist/MidiFighter3D/MidiFighter3D

One-File Build (Optional)
-------------------------
For a single executable file:
   pyinstaller --onefile MidiFighter3D.spec

Note: One-file builds are slower to start but easier to distribute.

Data Files
----------
The spec file includes:
- config/ - Configuration files
- scripts/ - Automation scripts
- sounds/ - Audio files (commented out, add if needed)

Icons
-----
To add a custom icon:
1. Create an icon file (icon.ico for Windows, icon.icns for macOS)
2. Uncomment the icon line in MidiFighter3D.spec
3. Rebuild

Windows Taskbar Icon
--------------------
For proper taskbar icons on Windows, the app uses:
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID()

This is already implemented in main_window.py.

macOS App Bundle
----------------
For macOS .app bundles:
   pyinstaller --windowed --osx-bundle-identifier com.yourcompany.midifighter3d MidiFighter3D.spec

Distribution
------------
After building:
1. Windows: Use InstallForge or similar to create an installer
2. macOS: Create a .dmg file
3. Linux: Create an AppImage or distribute the folder

Troubleshooting
---------------
- If imports are missing, add them to hiddenimports in the spec file
- If data files aren't found, check the datas tuple in the spec file
- For debugging, use console=True temporarily to see error messages

Nix Users
---------
If using Nix, you may need to enter a nix-shell with PyInstaller:
   nix-shell -p python3 python3Packages.pyinstaller
   pyinstaller MidiFighter3D.spec

Size Optimization
----------------
The spec file excludes unnecessary modules:
- matplotlib
- tkinter
- PIL
- scipy
- pandas

Add more to the excludes list if needed.

Code Signing (Optional)
-----------------------
For signed executables:
- Windows: Use signtool or similar
- macOS: Use codesign with Apple Developer ID

See PyInstaller documentation for details.
"""
