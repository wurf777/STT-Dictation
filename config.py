# STT Dictation — Configuration with JSON persistence

import json
import os
import sys
import sounddevice as sd


def app_data_dir() -> str:
    """Return the writable app data directory for source and frozen builds."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def resolve_app_path(path: str) -> str:
    """Resolve a relative app data path against the writable app data directory."""
    if os.path.isabs(path):
        return path
    return os.path.join(app_data_dir(), path)


# Path to user settings file (next to the script or installed exe)
_SETTINGS_FILE = resolve_app_path("settings.json")

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
    "vocabulary": [],                  # Ord/namn som nudgar modellen (initial_prompt)
    "replacements": {},                # {"fel stavning": "rätt stavning"} — efterbehandling
    "restore_clipboard_after_paste": True,
    "clipboard_paste_delay_ms": 75,
    "clipboard_restore_delay_ms": 500,
    "smart_leading_space_enabled": True,
    "smart_leading_space_window_seconds": 90,
    "smart_remove_previous_period_enabled": True,
    "repaste_hotkey": "F10",
    "correction_hotkey": "ctrl+alt+f10",
    "dictation_learning_enabled": True,
    "dictation_history_path": os.path.join("data", "dictation_history.jsonl"),
    "learning_basket_path": os.path.join("data", "learning_basket.jsonl"),
    "post_process_enabled": True,
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
