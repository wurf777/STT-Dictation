"""System tray icon using pystray — provides status indicator and exit option."""

import os
import sys
import threading
from PIL import Image
import pystray


def _load_icon_image():
    """Load icon.png — checks _MEIPASS (PyInstaller _internal/) then exe dir."""
    candidates = []
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            candidates.append(os.path.join(sys._MEIPASS, "icon.png"))
        candidates.append(os.path.join(os.path.dirname(sys.executable), "icon.png"))
    else:
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png"))
    for path in candidates:
        if os.path.exists(path):
            return Image.open(path).convert("RGBA")
    raise FileNotFoundError(f"icon.png hittades inte. Sökte i: {candidates}")


class TrayIcon:
    def __init__(self, on_exit=None, on_settings=None, on_vocabulary=None):
        self._on_exit = on_exit
        self._on_settings = on_settings
        self._on_vocabulary = on_vocabulary
        self._icon = None

    def start(self):
        """Start the system tray icon (blocking — run in a thread or as the main loop)."""
        menu = pystray.Menu(
            pystray.MenuItem("STT Dictation", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Ordlista...", self._vocabulary_clicked),
            pystray.MenuItem("Inställningar...", self._settings_clicked),
            pystray.MenuItem("Avsluta", self._exit_clicked),
        )
        self._icon = pystray.Icon(
            name="stt-dictation",
            icon=_load_icon_image(),
            title="STT Dictation — Redo",
            menu=menu,
        )
        self._icon.run()

    def update_title(self, title: str):
        """Update the hover tooltip text."""
        if self._icon:
            self._icon.title = title

    def stop(self):
        """Stop the tray icon."""
        if self._icon:
            self._icon.stop()

    def _settings_clicked(self, icon, item):
        if self._on_settings:
            self._on_settings()

    def _vocabulary_clicked(self, icon, item):
        if self._on_vocabulary:
            self._on_vocabulary()

    def _exit_clicked(self, icon, item):
        # on_exit callback (shutdown) calls tray.stop(), so no need to call it here
        if self._on_exit:
            self._on_exit()
