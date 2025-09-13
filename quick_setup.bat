@echo off
echo Audio Priority Manager - Quick Setup
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.8+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
echo.

REM Install required packages
pip install pycaw>=20230407 comtypes>=1.2.0 PyQt6>=6.6.0 pystray>=0.19.4 Pillow>=10.0.0 pyinstaller>=6.0.0

if %errorlevel% neq 0 (
    echo.
    echo Failed to install some dependencies.
    echo Try running as Administrator or use:
    echo   pip install --user [package_name]
    echo.
    pause
    exit /b 1
)

echo.
echo ✓ Setup completed successfully!
echo.
echo You can now use:
echo   python app.py                    (GUI mode)
echo   python app.py --priority vlc.exe (CLI mode)  
echo   python build_exe.py              (Build EXE)
echo.
pause
