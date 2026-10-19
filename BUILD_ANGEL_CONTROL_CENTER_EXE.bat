@echo off
setlocal
cd /d "%~dp0"
title Build LocalAI-Angel Control Center EXE
color 0B
echo ============================================================
echo   BUILD LOCALAI-ANGEL CONTROL CENTER EXE
echo ============================================================
echo.
where py >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python launcher 'py' was not found.
  echo Install Python 3.10+ and enable the Python launcher.
  pause
  exit /b 1
)
echo Installing/updating PyInstaller...
py -3 -m pip install --upgrade pyinstaller
if errorlevel 1 (
  echo ERROR: Could not install PyInstaller.
  pause
  exit /b 1
)
echo.
echo Removing stale build output...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist AngelControlCenter.spec del /f /q AngelControlCenter.spec
echo.
echo Building standalone Windows GUI executable...
py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name AngelControlCenter ANGEL_CONTROL_CENTER.py
if errorlevel 1 (
  echo ERROR: EXE build failed.
  pause
  exit /b 1
)
echo.
echo SUCCESS: dist\AngelControlCenter.exe
echo Copy this EXE into the repository root beside the three BAT files.
pause
endlocal
