"""Global hotkey manager — push-to-talk using the keyboard library.

Supports both single keys (F9) and combinations (ctrl+shift+f9).
"""

import keyboard


class HotkeyManager:
    def __init__(self, on_press=None, on_release=None, hotkey="F9"):
        self.hotkey = hotkey
        self._on_press = on_press
        self._on_release = on_release
        self._is_pressed = False
        self._hook = None
        self._is_combo = "+" in hotkey

    def start(self):
        """Start listening for the global hotkey."""
        if self._is_combo:
            # For combinations like ctrl+shift+f9, use add_hotkey
            # which handles modifier tracking for us
            self._hook = keyboard.add_hotkey(
                self.hotkey, self._combo_pressed, suppress=False, trigger_on_release=False
            )
            # For combos we also need to detect release of the main key
            # (last key in the combo)
            self._main_key = self.hotkey.split("+")[-1].strip()
            self._release_hook = keyboard.on_release_key(
                self._main_key, self._combo_released, suppress=False
            )
        else:
            # For single keys, use a global hook for clean press/release
            self._hook = keyboard.hook(self._on_event, suppress=False)
            self._release_hook = None

        print(f"[hotkey] Lyssnar på {self.hotkey} (håll = spela in, släpp = transkribera)")

    def stop(self):
        """Stop listening."""
        if self._hook is not None:
            keyboard.unhook(self._hook)
            self._hook = None
        if getattr(self, '_release_hook', None) is not None:
            try:
                keyboard.unhook(self._release_hook)
            except (KeyError, ValueError):
                pass
            self._release_hook = None
        self._is_pressed = False

    # ── Single-key mode ──────────────────────────────────────

    def _on_event(self, event):
        if event.name.lower() != self.hotkey.lower():
            return

        if event.event_type == keyboard.KEY_DOWN:
            if self._is_pressed:
                return
            self._is_pressed = True
            if self._on_press:
                self._on_press()
        elif event.event_type == keyboard.KEY_UP:
            if not self._is_pressed:
                return
            self._is_pressed = False
            if self._on_release:
                self._on_release()

    # ── Combo mode ───────────────────────────────────────────

    def _combo_pressed(self):
        if self._is_pressed:
            return
        self._is_pressed = True
        if self._on_press:
            self._on_press()

    def _combo_released(self, event):
        if not self._is_pressed:
            return
        self._is_pressed = False
        if self._on_release:
            self._on_release()
