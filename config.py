# STT Dictation — Configuration with JSON persistence

import json
import os
import sounddevice as sd

# Path to user settings file (next to the script)
_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

# ── Defaults ─────────────────────────────────────────────────
DEFAULTS = {
    "hotkey": "F9",
    "whisper_model": "KBLab/kb-whisper-medium",
    "language": "sv",
    "output_mode": "auto_paste",       # "auto_paste" | "clipboard_only"
    "sample_rate": 16000,
    "audio_device": None,              # None = system default
    "show_feedback_window": True,
    "feedback_window_position": "bottom-right",
    "feedback_auto_close_delay": 2500,
    "beam_size": 5,                    # 1 = snabbast, 5 = bäst kvalitet
}

# ── Load / Save ──────────────────────────────────────────────
_settings: dict = {}


def _load():
    global _settings
    _settings = dict(DEFAULTS)
    if os.path.exists(_SETTINGS_FILE):
        try:
            with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            _settings.update(saved)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[config] Kunde inte läsa {_SETTINGS_FILE}: {e}")


def save():
    """Save current settings (only non-default values) to settings.json."""
    to_save = {k: v for k, v in _settings.items() if v != DEFAULTS.get(k)}
    try:
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"[config] Kunde inte spara inställningar: {e}")


def get(key: str):
    """Get a setting value."""
    return _settings.get(key, DEFAULTS.get(key))


def set(key: str, value):
    """Set a setting value."""
    _settings[key] = value


def get_all() -> dict:
    """Return a copy of all current settings."""
    return dict(_settings)


# ── Audio device helpers ─────────────────────────────────────
def get_input_devices():
    """Return a list of available audio input devices."""
    devices = []
    for i, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            devices.append({"index": i, "name": dev["name"]})
    return devices


# ── Convenience aliases (for backward compat) ───────────────
# These read from the live settings dict so they always reflect current values.

def _make_property(key):
    return property(lambda self: get(key))


# Module-level shortcuts — use config.get("hotkey") or these constants
# Updated on load, and after set() + save()
_load()

HOTKEY = get("hotkey")
WHISPER_MODEL = get("whisper_model")
LANGUAGE = get("language")
OUTPUT_MODE = get("output_mode")
SAMPLE_RATE = get("sample_rate")
SHOW_FEEDBACK_WINDOW = get("show_feedback_window")
FEEDBACK_WINDOW_POSITION = get("feedback_window_position")
FEEDBACK_AUTO_CLOSE_DELAY = get("feedback_auto_close_delay")
