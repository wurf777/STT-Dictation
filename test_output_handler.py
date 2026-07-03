import time

import output_handler
from output_handler import (
    looks_like_sentence_continuation,
    should_prefix_continuation_space,
    should_remove_previous_period_for_continuation,
)


def test_prefixes_space_for_recent_continuation():
    assert should_prefix_continuation_space(
        "och sedan fortsätter jag",
        previous_text="Det här var första delen.",
        elapsed_seconds=12,
        window_seconds=90,
    )


def test_does_not_prefix_space_after_timeout():
    assert not should_prefix_continuation_space(
        "och sedan fortsätter jag",
        previous_text="Det här var första delen.",
        elapsed_seconds=120,
        window_seconds=90,
    )


def test_does_not_prefix_space_before_punctuation():
    assert not should_prefix_continuation_space(
        ", och sedan fortsätter jag",
        previous_text="Det här var första delen",
        elapsed_seconds=12,
        window_seconds=90,
    )


def test_does_not_prefix_space_when_previous_already_has_space():
    assert not should_prefix_continuation_space(
        "och sedan fortsätter jag",
        previous_text="Det här var första delen. ",
        elapsed_seconds=12,
        window_seconds=90,
    )


def test_removes_single_previous_period_for_continuation():
    assert should_remove_previous_period_for_continuation(
        "Det här var första delen.",
        "och sedan fortsätter jag",
    )


def test_does_not_remove_ellipsis():
    assert not should_remove_previous_period_for_continuation("Det här var första delen...")


def test_does_not_remove_question_mark_or_exclamation():
    assert not should_remove_previous_period_for_continuation("Är det här första delen?")
    assert not should_remove_previous_period_for_continuation("Det här var första delen!")


def test_does_not_remove_period_before_new_sentence():
    assert not should_remove_previous_period_for_continuation(
        "Det här var första delen.",
        "Det här är en ny mening.",
    )


def test_detects_capitalized_continuation_word():
    assert looks_like_sentence_continuation("Och sedan fortsätter jag")
    assert not looks_like_sentence_continuation("Det här är en ny mening")


def test_output_text_removes_previous_period_before_paste():
    old_config = output_handler.config
    old_pyperclip = output_handler.pyperclip
    old_pyautogui = output_handler.pyautogui
    old_last_auto_paste = output_handler._last_auto_paste

    class FakeConfig:
        values = {
            "output_mode": "auto_paste",
            "restore_clipboard_after_paste": False,
            "clipboard_paste_delay_ms": 0,
            "smart_leading_space_enabled": True,
            "smart_leading_space_window_seconds": 90,
            "smart_remove_previous_period_enabled": True,
        }

        @classmethod
        def get(cls, key):
            return cls.values.get(key)

    class FakeClipboard:
        copied = []

        @classmethod
        def copy(cls, text):
            cls.copied.append(text)

        @staticmethod
        def paste():
            return "tidigare urklipp"

    class FakeKeyboard:
        actions = []

        @classmethod
        def press(cls, key):
            cls.actions.append(("press", key))

        @classmethod
        def hotkey(cls, *keys):
            cls.actions.append(("hotkey", keys))

    try:
        output_handler.config = FakeConfig
        output_handler.pyperclip = FakeClipboard
        output_handler.pyautogui = FakeKeyboard
        output_handler._last_auto_paste = {
            "text": "Det här var första delen.",
            "time": time.monotonic(),
        }

        pasted = output_handler.output_text("och sedan fortsätter jag", mode="auto_paste")

        assert pasted == " och sedan fortsätter jag"
        assert FakeClipboard.copied == [" och sedan fortsätter jag"]
        assert FakeKeyboard.actions == [
            ("press", "backspace"),
            ("hotkey", ("ctrl", "v")),
        ]
    finally:
        output_handler.config = old_config
        output_handler.pyperclip = old_pyperclip
        output_handler.pyautogui = old_pyautogui
        output_handler._last_auto_paste = old_last_auto_paste
