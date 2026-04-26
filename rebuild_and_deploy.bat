@echo off
echo ============================================
echo  Bygger STT Dictation (tkinter-fix)
echo ============================================
cd /d "%~dp0"

echo.
echo Aktiverar virtuell miljö...
call .venv\Scripts\activate.bat

echo.
echo Kör PyInstaller (--clean)...
pyinstaller "STT Dictation.spec" --clean

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo FEL: PyInstaller misslyckades!
    pause
    exit /b 1
)

echo.
echo Kopierar till C:\Program_USB\STT Dictation...
call deploy.bat

echo.
echo ============================================
echo  KLART! Testa appen nu.
echo ============================================
pause
