"""Output handler - paste transcribed text into the active window."""

import time
from typing import Optional

import pyautogui
import pyperclip

import config


_last_output_text = ""
_last_auto_paste = None


def output_text(
    text: str,
    mode: Optional[str] = None,
    allow_smart_spacing: bool = True,
):
    """Output transcribed text and remember it for repaste."""
    global _last_output_text

    if not text:
        return ""

    _last_output_text = text

    if mode is None:
        mode = config.get("output_mode")

    remove_previous_character = _should_remove_previous_period(
        text,
        mode=mode,
        allow_smart_spacing=allow_smart_spacing,
    )
    text_to_paste = _prepare_output_text(
        text,
        mode=mode,
        allow_smart_spacing=allow_smart_spacing,
        already_removing_period=remove_previous_character,
    )

    restore_clipboard = (
        mode == "auto_paste"
        and bool(config.get("restore_clipboard_after_paste"))
    )
    previous_clipboard = _safe_paste() if restore_clipboard else None

    _paste_via_clipboard(
        text_to_paste,
        mode,
        remove_previous_character=remove_previous_character,
    )

    _remember_auto_paste(text_to_paste, mode)

    if restore_clipboard and previous_clipboard is not None:
        time.sleep(_delay_seconds("clipboard_restore_delay_ms", 500))
        pyperclip.copy(previous_clipboard)

    return text_to_paste


def output_last_text(mode: Optional[str] = None) -> bool:
    """Paste the most recent dictation again. Returns True if text existed."""
    if not _last_output_text:
        return False
    output_text(_last_output_text, mode=mode, allow_smart_spacing=False)
    return True


def get_last_output_text() -> str:
    """Return the most recent dictation text held by the app."""
    return _last_output_text


def _paste_via_clipboard(
    text: str,
    mode: Optional[str],
    remove_previous_character: bool = False,
):
    pyperclip.copy(text)

    if mode == "auto_paste":
        time.sleep(_delay_seconds("clipboard_paste_delay_ms", 75))
        if remove_previous_character:
            pyautogui.press("backspace")
            time.sleep(_delay_seconds("clipboard_paste_delay_ms", 75))
        pyautogui.hotkey("ctrl", "v")


def _prepare_output_text(
    text: str,
    mode: Optional[str],
    allow_smart_spacing: bool,
    already_removing_period: bool = False,
) -> str:
    if already_removing_period or _should_add_leading_space(text, mode, allow_smart_spacing):
        return " " + text
    return text


def _should_add_leading_space(
    text: str,
    mode: Optional[str],
    allow_smart_spacing: bool = True,
) -> bool:
    if mode != "auto_paste" or not allow_smart_spacing:
        return False
    if not bool(config.get("smart_leading_space_enabled")):
        return False
    if not _last_auto_paste:
        return False

    elapsed = time.monotonic() - _last_auto_paste["time"]
    window = _number_setting("smart_leading_space_window_seconds", 90)
    return should_prefix_continuation_space(
        text,
        previous_text=_last_auto_paste["text"],
        elapsed_seconds=elapsed,
        enabled=True,
        window_seconds=window,
    )


def should_prefix_continuation_space(
    text: str,
    previous_text: str,
    elapsed_seconds: float,
    enabled: bool = True,
    window_seconds: float = 90,
) -> bool:
    """Return True when a new dictation likely continues after the previous paste."""
    if not enabled:
        return False
    if not text or not previous_text:
        return False
    if elapsed_seconds < 0 or elapsed_seconds > window_seconds:
        return False
    if previous_text[-1].isspace() or text[0].isspace():
        return False
    if text[0] in ".,;:!?)]}%":
        return False
    return True


def _should_remove_previous_period(
    text: str,
    mode: Optional[str],
    allow_smart_spacing: bool = True,
) -> bool:
    if not bool(config.get("smart_remove_previous_period_enabled")):
        return False
    if not _should_add_leading_space(text, mode, allow_smart_spacing):
        return False

    previous_text = _last_auto_paste["text"].rstrip()
    return should_remove_previous_period_for_continuation(previous_text, text)


def should_remove_previous_period_for_continuation(
    previous_text: str,
    next_text: str = "",
) -> bool:
    """Return True if the previous paste ended with one removable sentence period."""
    if not previous_text.endswith("."):
        return False
    if previous_text.endswith("..."):
        return False
    if next_text and not looks_like_sentence_continuation(next_text):
        return False
    return True


def looks_like_sentence_continuation(text: str) -> bool:
    """Return True when text starts like a continuation rather than a new sentence."""
    stripped = text.lstrip()
    if not stripped:
        return False

    first_char = stripped[0]
    if first_char.islower():
        return True

    first_word = stripped.split(maxsplit=1)[0].strip(".,;:!?()[]{}\"'")
    continuation_words = {
        "att",
        "och",
        "men",
        "som",
        "för",
        "därför",
        "så",
        "eftersom",
        "när",
        "om",
        "eller",
        "utan",
        "vilket",
        "vilka",
        "vilken",
    }
    return first_word.lower() in continuation_words


def _remember_auto_paste(text: str, mode: Optional[str]):
    global _last_auto_paste
    if mode != "auto_paste":
        return
    _last_auto_paste = {
        "text": text,
        "time": time.monotonic(),
    }


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


def _number_setting(key: str, default):
    value = config.get(key)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
