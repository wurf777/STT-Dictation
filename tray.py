"""System tray icon using pystray — provides status indicator and exit option."""

import threading
from PIL import Image, ImageDraw
import pystray


def _create_icon_image(color="#4fc3f7", size=64):
    """Create a simple microphone-style icon."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Rounded rectangle body
    draw.rounded_rectangle(
        [size * 0.3, size * 0.1, size * 0.7, size * 0.55],
        radius=size * 0.15,
        fill=color,
    )
    # Stand
    draw.arc(
        [size * 0.2, size * 0.35, size * 0.8, size * 0.7],
        start=0, end=180, fill=color, width=3,
    )
    # Stem
    cx = size // 2
    draw.line([(cx, size * 0.7), (cx, size * 0.85)], fill=color, width=3)
    # Base
    draw.line([(size * 0.3, size * 0.85), (size * 0.7, size * 0.85)], fill=color, width=3)
    return img


class TrayIcon:
    def __init__(self, on_exit=None, on_settings=None):
        self._on_exit = on_exit
        self._on_settings = on_settings
        self._icon = None

    def start(self):
        """Start the system tray icon (blocking — run in a thread or as the main loop)."""
        menu = pystray.Menu(
            pystray.MenuItem("STT Dictation", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Inställningar...", self._settings_clicked),
            pystray.MenuItem("Avsluta", self._exit_clicked),
        )
        self._icon = pystray.Icon(
            name="stt-dictation",
            icon=_create_icon_image(),
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

    def _exit_clicked(self, icon, item):
        # on_exit callback (shutdown) calls tray.stop(), so no need to call it here
        if self._on_exit:
            self._on_exit()
