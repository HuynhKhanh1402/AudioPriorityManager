"""
Setup script for Audio Priority Manager
Handles installation and environment setup
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    
    requirements = [
        'pycaw>=20230407',
        'comtypes>=1.2.0', 
        'PyQt6>=6.6.0',
        'pystray>=0.19.4',
        'Pillow>=10.0.0',
        'pyinstaller>=6.0.0'
    ]
    
    for requirement in requirements:
        print(f"Installing {requirement}...")
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', requirement
            ], check=True, capture_output=True)
            print(f"✓ {requirement}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {requirement}: {e}")
            return False
    
    return True

def check_dependencies():
    """Check if all dependencies are available"""
    print("Checking dependencies...")
    
    deps = {
        'pycaw': 'pycaw.pycaw',
        'comtypes': 'comtypes',
        'PyQt6': 'PyQt6.QtWidgets',
        'pystray': 'pystray',
        'PIL': 'PIL'
    }
    
    missing = []
    for name, module in deps.items():
        try:
            __import__(module)
            print(f"✓ {name}")
        except ImportError:
            print(f"✗ {name} (missing)")
            missing.append(name)
    
    return len(missing) == 0, missing

def create_dev_launcher():
    """Create development launcher script"""
    launcher_content = '''@echo off
title Audio Priority Manager - Development
echo Audio Priority Manager - Development Mode
echo =========================================
echo.
echo Choose an option:
echo 1. Run GUI (Development)
echo 2. Run CLI (Development) 
echo 3. Build EXE files
echo 4. Install requirements
echo 5. Exit
echo.

:menu
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" (
    echo Starting GUI mode...
    python app.py --gui
    goto end
)
if "%choice%"=="2" (
    echo Starting CLI mode...
    echo Enter CLI arguments (e.g., --priority vlc.exe):
    set /p args="Arguments: "
    python app.py %args%
    goto end
)
if "%choice%"=="3" (
    echo Building executable files...
    python build_exe.py
    goto end
)
if "%choice%"=="4" (
    echo Installing requirements...
    python setup.py
    goto end
)
if "%choice%"=="5" (
    goto end
)

echo Invalid choice. Please try again.
goto menu

:end
pause
'''
    
    with open('dev_launcher.bat', 'w') as f:
        f.write(launcher_content)
    print("Created development launcher: dev_launcher.bat")

def create_project_structure():
    """Ensure project structure is correct"""
    dirs = [
        'src',
        'assets', 
        'build',
        'dist'
    ]
    
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"✓ Directory: {dir_name}/")

def main():
    """Main setup function"""
    print("Audio Priority Manager Setup")
    print("=" * 35)
    
    # Create project structure
    create_project_structure()
    
    # Check current dependencies
    deps_ok, missing = check_dependencies()
    
    if not deps_ok:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        response = input("Install missing dependencies? (y/n): ").lower()
        
        if response == 'y':
            if install_requirements():
                print("\n✓ All dependencies installed successfully!")
            else:
                print("\n✗ Some dependencies failed to install.")
                return False
        else:
            print("Setup cancelled. Some features may not work.")
            return False
    else:
        print("\n✓ All dependencies are available!")
    
    # Create development tools
    create_dev_launcher()
    
    print("\nSetup completed successfully!")
    print("\nNext steps:")
    print("1. Run 'dev_launcher.bat' for development")
    print("2. Or run 'python app.py' for GUI mode")
    print("3. Or run 'python app.py --priority vlc.exe' for CLI mode")
    print("4. Run 'python build_exe.py' to create EXE files")
    
    return True

if __name__ == "__main__":
    main()
