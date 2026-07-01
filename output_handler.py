"""Output handler - paste transcribed text into the active window."""

import time
from typing import Optional

import pyautogui
import pyperclip

import config


_last_output_text = ""


def output_text(text: str, mode: Optional[str] = None):
    """Output transcribed text and remember it for repaste."""
    global _last_output_text

    if not text:
        return

    _last_output_text = text

    if mode is None:
        mode = config.get("output_mode")

    restore_clipboard = (
        mode == "auto_paste"
        and bool(config.get("restore_clipboard_after_paste"))
    )
    previous_clipboard = _safe_paste() if restore_clipboard else None

    _paste_via_clipboard(text, mode)

    if restore_clipboard and previous_clipboard is not None:
        time.sleep(_delay_seconds("clipboard_restore_delay_ms", 500))
        pyperclip.copy(previous_clipboard)


def output_last_text(mode: Optional[str] = None) -> bool:
    """Paste the most recent dictation again. Returns True if text existed."""
    if not _last_output_text:
        return False
    output_text(_last_output_text, mode=mode)
    return True


def get_last_output_text() -> str:
    """Return the most recent dictation text held by the app."""
    return _last_output_text


def _paste_via_clipboard(text: str, mode: Optional[str]):
    pyperclip.copy(text)

    if mode == "auto_paste":
        time.sleep(_delay_seconds("clipboard_paste_delay_ms", 75))
        pyautogui.hotkey("ctrl", "v")


def _safe_paste() -> Optional[str]:
    try:
        return pyperclip.paste()
    except pyperclip.PyperclipException:
        return None


def _delay_seconds(key: str, default_ms: int) -> float:
    value = config.get(key)
    try:
        milliseconds = int(value)
    except (TypeError, ValueError):
        milliseconds = default_ms
    return max(milliseconds, 0) / 1000
