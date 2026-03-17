"""Output handler — paste transcribed text into the active window."""

import time
import pyperclip
import pyautogui

import config


from typing import Optional


def output_text(text: str, mode: Optional[str] = None):
    """Output transcribed text via clipboard and optionally auto-paste."""
    if not text:
        return

    if mode is None:
        mode = config.get("output_mode")

    pyperclip.copy(text)

    if mode == "auto_paste":
        time.sleep(0.05)
        pyautogui.hotkey("ctrl", "v")
