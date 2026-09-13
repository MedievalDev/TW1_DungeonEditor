@echo off
rem Build TW1DungeonEditor.exe with PyInstaller (one file, no console).
rem Needs Python 3 with PyInstaller:  py -m pip install pyinstaller
rem Result: dist\TW1DungeonEditor.exe
cd /d "%~dp0"
py -3 -m PyInstaller --noconfirm --clean build_exe.spec
if errorlevel 1 (
    echo BUILD FAILED
    exit /b 1
)
echo.
echo Built: %~dp0dist\TW1DungeonEditor.exe
