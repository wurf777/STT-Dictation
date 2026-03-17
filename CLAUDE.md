# STT Dictation

Push-to-talk-dikteringsverktyg for Windows. Hold a global hotkey (F9), speak, release — speech is transcribed via KB-Whisper and pasted into the active window.

## Tech Stack

- **Python** (same environment as the TTS app)
- **faster-whisper** with KB-Whisper model (`KBLab/kb-whisper-medium`)
- **sounddevice** + **numpy** for audio recording
- **keyboard** for global hotkey
- **pyperclip** + **pyautogui** for clipboard/auto-paste output
- **pystray** + **Pillow** for system tray
- **tkinter** for live feedback window (built-in, no extra deps)

## Project Structure

```
stt-dictation/
├── main.py              # Entry point, initializes everything
├── recorder.py          # Audio recording via sounddevice
├── transcriber.py       # Whisper transcription (with streaming)
├── output_handler.py    # Clipboard + autotype
├── hotkey_manager.py    # Global hotkey handling
├── feedback_window.py   # Live transcription window (tkinter)
├── tray.py              # System tray icon and menu
├── config.py            # Settings (hotkey, model, language etc.)
└── requirements.txt
```

## Architecture / Flow

1. App starts → loads Whisper model in background (once) → appears in system tray
2. User holds hotkey (F9) → recording starts
3. Hotkey released → recording stops, audio sent to Whisper
4. Whisper transcribes → returns text (Swedish)
5. Text output via auto-paste (clipboard + Ctrl+V) or clipboard-only mode
6. Optional: live feedback window shows progressive transcription

## Key Configuration (config.py)

- `HOTKEY = "F9"` — global push-to-talk key
- `WHISPER_MODEL = "KBLab/kb-whisper-medium"` — medium for balance of speed/quality
- `LANGUAGE = "sv"` — Swedish
- `OUTPUT_MODE = "auto_paste"` — `"auto_paste"` or `"clipboard_only"`
- `SAMPLE_RATE = 16000` — Whisper expects 16kHz
- `SHOW_FEEDBACK_WINDOW = True` — live transcription overlay
- `FEEDBACK_WINDOW_POSITION = "bottom-right"`

## Conventions

- Language in code: English for code, Swedish is fine for user-facing strings and comments where natural
- Keep the app lightweight and discreet — no unnecessary windows, minimal latency
- Use `queue.Queue` for thread communication (recorder → transcriber → feedback window)
- Feedback window uses tkinter `overrideredirect(True)` + `wm_attributes("-topmost", True)`
- faster-whisper with `word_timestamps=True` for progressive text display
- Silent fallback on errors (no crashes), use tray notifications for error feedback

## Implementation Order

1. `recorder.py` — basic start/stop recording
2. `transcriber.py` — load KB-Whisper, transcribe audio buffer, streaming support
3. Wire recorder + transcriber in `main.py`, test via CLI
4. `hotkey_manager.py` — global hotkey push-to-talk
5. `output_handler.py` — clipboard + auto-paste
6. `feedback_window.py` — live transcription window
7. `tray.py` — tray icon with exit option
8. Error handling (mic unavailable, model not loaded, etc.)

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py
```

## Notes

- The `keyboard` library requires admin/elevated privileges on some systems for global hotkeys
- Model downloads from Hugging Face automatically on first run
- Target GPU: ASUS G14 — medium model should work fine with available VRAM
