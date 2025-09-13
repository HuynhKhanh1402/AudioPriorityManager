"""
Build script for Audio Priority Manager
Creates executable files using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build():
    """Clean previous build artifacts"""
    build_dirs = ['build', 'dist', '__pycache__']
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Cleaned {dir_name}/")
    
    # Clean .spec files
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"Removed {spec_file}")

def create_icon():
    """Create a simple icon for the application"""
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple icon
        img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw a circle with audio waves
        draw.ellipse([20, 20, 108, 108], fill=(61, 174, 233, 255))
        draw.ellipse([30, 30, 98, 98], fill=(255, 255, 255, 255))
        draw.ellipse([40, 40, 88, 88], fill=(61, 174, 233, 255))
        
        # Add some wave lines
        for i in range(3):
            y = 45 + i * 10
            draw.rectangle([50, y, 78, y+3], fill=(255, 255, 255, 255))
        
        # Save as ICO file
        icon_path = 'assets/icon.ico'
        os.makedirs('assets', exist_ok=True)
        img.save(icon_path, 'ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128)])
        print(f"Created icon: {icon_path}")
        return icon_path
    except ImportError:
        print("Pillow not available, skipping icon creation")
        return None

def build_gui_version():
    """Build GUI version"""
    print("Building GUI version...")
    
    icon_path = create_icon()
    
    cmd = [
        'pyinstaller',
        '--onefile',                    # Single executable
        '--windowed',                   # No console window
        '--name', 'AudioPriorityGUI',   # Output name
        '--distpath', 'dist',           # Output directory
        '--workpath', 'build',          # Build directory
        '--clean',                      # Clean cache
        '--add-data', 'src;src',        # Include src directory
    ]
    
    if icon_path:
        cmd.extend(['--icon', icon_path])
    
    # Hidden imports for PyQt6
    cmd.extend([
        '--hidden-import', 'PyQt6.QtCore',
        '--hidden-import', 'PyQt6.QtGui', 
        '--hidden-import', 'PyQt6.QtWidgets',
        '--hidden-import', 'pycaw.pycaw',
        '--hidden-import', 'comtypes'
    ])
    
    cmd.append('app.py')
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ GUI version built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to build GUI version: {e}")
        return False

def build_cli_version():
    """Build CLI version"""
    print("Building CLI version...")
    
    cmd = [
        'pyinstaller',
        '--onefile',                    # Single executable
        '--console',                    # Keep console window
        '--name', 'AudioPriorityCLI',   # Output name
        '--distpath', 'dist',           # Output directory
        '--workpath', 'build',          # Build directory
        '--clean',                      # Clean cache
        '--add-data', 'src;src',        # Include src directory
        '--hidden-import', 'pycaw.pycaw',
        '--hidden-import', 'comtypes'
    ]
    
    # Create a CLI-only entry point
    cli_entry = '''
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

if __name__ == "__main__":
    from app import run_cli
    run_cli()
'''
    
    with open('cli_entry.py', 'w') as f:
        f.write(cli_entry)
    
    cmd.append('cli_entry.py')
    
    try:
        subprocess.run(cmd, check=True)
        print("✓ CLI version built successfully!")
        os.remove('cli_entry.py')  # Clean up
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to build CLI version: {e}")
        if os.path.exists('cli_entry.py'):
            os.remove('cli_entry.py')
        return False

def create_installer_script():
    """Create a simple installer script"""
    installer_content = '''@echo off
echo Audio Priority Manager Installer
echo ================================
echo.
echo Installing Audio Priority Manager...
echo.

if not exist "%PROGRAMFILES%\\AudioPriority" (
    mkdir "%PROGRAMFILES%\\AudioPriority"
)

copy "AudioPriorityGUI.exe" "%PROGRAMFILES%\\AudioPriority\\" >nul
copy "AudioPriorityCLI.exe" "%PROGRAMFILES%\\AudioPriority\\" >nul

echo Creating shortcuts...
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\\create_shortcut.vbs"
echo sLinkFile = "%USERPROFILE%\\Desktop\\Audio Priority Manager.lnk" >> "%TEMP%\\create_shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\\create_shortcut.vbs"
echo oLink.TargetPath = "%PROGRAMFILES%\\AudioPriority\\AudioPriorityGUI.exe" >> "%TEMP%\\create_shortcut.vbs"
echo oLink.Save >> "%TEMP%\\create_shortcut.vbs"
cscript //NoLogo "%TEMP%\\create_shortcut.vbs"
del "%TEMP%\\create_shortcut.vbs"

echo.
echo Installation complete!
echo Desktop shortcut created.
echo.
echo You can also run from command line:
echo   "%PROGRAMFILES%\\AudioPriority\\AudioPriorityGUI.exe" (GUI)
echo   "%PROGRAMFILES%\\AudioPriority\\AudioPriorityCLI.exe" (CLI)
echo.
pause
'''
    
    with open('dist/install.bat', 'w') as f:
        f.write(installer_content)
    print("Created installer script: dist/install.bat")

def create_readme():
    """Create README for distribution"""
    readme_content = '''# Audio Priority Manager

## What is this?
Audio Priority Manager automatically ducks (lowers volume of) other audio when your priority application is playing sound.

Perfect for:
- Gaming (duck music when game has audio)  
- Video calls (duck background audio during meetings)
- Media consumption (duck notifications during movies)

## Quick Start

### GUI Version (Recommended)
1. Double-click `AudioPriorityGUI.exe`
2. Enter your priority process (e.g., "vlc.exe", "spotify.exe") 
3. Configure settings as needed
4. Click "Start Ducking"
5. Minimize to system tray

### Command Line Version
```
AudioPriorityCLI.exe --priority "vlc.exe" --duck-to 0.2
```

## Installation
Run `install.bat` as Administrator to install system-wide.

## Configuration
- **Priority Process**: The application that triggers ducking (e.g., vlc.exe)
- **Duck to Volume**: Target volume for other audio (0.0 = mute, 1.0 = full)
- **Threshold**: How loud audio must be to count as "active"
- **Attack/Release**: How quickly ducking starts/stops

## Advanced Features
- System tray integration
- Process-specific targeting  
- Hysteresis to prevent rapid on/off switching
- Smooth volume fading
- Activity monitoring and logging

## Troubleshooting
- Make sure to run as Administrator for full access to audio sessions
- Check that process names include .exe extension
- Verify target applications are actually playing audio

## Requirements
- Windows 10/11
- Audio applications using WASAPI (most modern apps)
'''
    
    with open('dist/README.txt', 'w') as f:
        f.write(readme_content)
    print("Created README: dist/README.txt")

def main():
    """Main build function"""
    print("Audio Priority Manager Build Script")
    print("=" * 40)
    
    # Check if pyinstaller is available
    try:
        subprocess.run(['pyinstaller', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
    
    # Clean previous builds
    clean_build()
    
    # Build both versions
    gui_success = build_gui_version()
    cli_success = build_cli_version()
    
    if gui_success or cli_success:
        print("\nCreating distribution files...")
        create_installer_script()
        create_readme()
        
        print("\nBuild Summary:")
        print("=" * 20)
        print(f"GUI Version: {'✓' if gui_success else '✗'}")
        print(f"CLI Version: {'✓' if cli_success else '✗'}")
        print(f"Output directory: dist/")
        
        if gui_success and cli_success:
            print("\n🎉 Build completed successfully!")
            print("\nDistribution files:")
            print("- AudioPriorityGUI.exe (GUI application)")  
            print("- AudioPriorityCLI.exe (Command-line tool)")
            print("- install.bat (Installer script)")
            print("- README.txt (Documentation)")
        else:
            print("\n⚠️  Some builds failed. Check error messages above.")
    else:
        print("\n❌ All builds failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
