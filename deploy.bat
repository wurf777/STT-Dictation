@echo off
set SOURCE=dist\STT Dictation
set TARGET=C:\Program_USB\STT Dictation

echo Kopierar till %TARGET%...
robocopy "%SOURCE%" "%TARGET%" /E /PURGE /XF settings.json
if %ERRORLEVEL% LEQ 7 (
    echo Klart!
) else (
    echo Fel vid kopiering. Kod: %ERRORLEVEL%
    pause
)
