"""Live feedback window — shows transcription progress as a floating overlay."""

import tkinter as tk
import threading
import queue
import ctypes

from config import FEEDBACK_WINDOW_POSITION, FEEDBACK_AUTO_CLOSE_DELAY


def _get_primary_monitor_work_area():
    """Get the work area (excluding taskbar) of the primary monitor via Win32 API."""
    try:
        import ctypes.wintypes
        rect = ctypes.wintypes.RECT()
        # SPI_GETWORKAREA = 0x0030
        ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
        return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        return 0, 0, 1920, 1040  # fallback


class FeedbackWindow:
    """Tkinter overlay window that runs on its own thread.

    Usage:
        fw = FeedbackWindow()
        fw.start()          # spawns the tkinter mainloop thread
        fw.show("🎙 ...")   # show window with text
        fw.update_text(txt) # update displayed text
        fw.hide()           # hide window
        fw.shutdown()       # destroy and join thread
    """

    def __init__(self, position=FEEDBACK_WINDOW_POSITION):
        self._position = position
        self._queue: queue.Queue = queue.Queue()
        self._thread = None
        self._root = None
        self._label = None
        self._auto_close_id = None

    # ── Public API (called from any thread) ──────────────────────

    def start(self):
        """Start the tkinter event loop on a daemon thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def show(self, text: str = "🎙 Spelar in..."):
        """Show the overlay with the given text."""
        self._queue.put(("show", text))

    def update_text(self, text: str):
        """Update the displayed text."""
        self._queue.put(("update", text))

    def hide(self):
        """Hide the overlay."""
        self._queue.put(("hide", None))

    def hide_after_delay(self, delay_ms: int = FEEDBACK_AUTO_CLOSE_DELAY):
        """Hide the overlay after a delay."""
        self._queue.put(("hide_delay", delay_ms))

    def shutdown(self):
        """Destroy the window and stop the thread."""
        self._queue.put(("quit", None))
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    # ── Internals (tkinter thread only) ──────────────────────────

    def _run(self):
        self._root = tk.Tk()
        self._root.withdraw()
        self._root.overrideredirect(True)
        self._root.wm_attributes("-topmost", True)
        self._root.wm_attributes("-alpha", 0.9)
        self._root.configure(bg="#1e1e2e")

        self._label = tk.Label(
            self._root,
            text="",
            font=("Segoe UI", 14),
            fg="#cdd6f4",
            bg="#1e1e2e",
            wraplength=500,
            justify="left",
            padx=16,
            pady=10,
        )
        self._label.pack()

        self._poll_queue()
        self._root.mainloop()

    def _poll_queue(self):
        """Process commands from the queue."""
        try:
            while True:
                cmd, data = self._queue.get_nowait()
                if cmd == "show":
                    self._do_show(data)
                elif cmd == "update":
                    self._do_update(data)
                elif cmd == "hide":
                    self._do_hide()
                elif cmd == "hide_delay":
                    self._schedule_auto_close(data)
                elif cmd == "quit":
                    self._root.quit()
                    return
        except queue.Empty:
            pass
        self._root.after(50, self._poll_queue)

    def _do_show(self, text: str):
        self._cancel_auto_close()
        self._label.config(text=text)
        self._root.deiconify()
        self._root.update_idletasks()
        self._position_window()

    def _do_update(self, text: str):
        self._label.config(text=text)
        self._position_window()

    def _do_hide(self):
        self._cancel_auto_close()
        self._root.withdraw()

    def _schedule_auto_close(self, delay_ms: int):
        self._cancel_auto_close()
        self._auto_close_id = self._root.after(delay_ms, self._do_hide)

    def _cancel_auto_close(self):
        if self._auto_close_id is not None:
            self._root.after_cancel(self._auto_close_id)
            self._auto_close_id = None

    def _position_window(self):
        self._root.update_idletasks()
        w = self._root.winfo_width()
        h = self._root.winfo_height()
        margin = 20

        # Use primary monitor work area (excludes taskbar, single monitor only)
        left, top, right, bottom = _get_primary_monitor_work_area()

        positions = {
            "bottom-right": (right - w - margin, bottom - h - margin),
            "bottom-left": (left + margin, bottom - h - margin),
            "top-right": (right - w - margin, top + margin),
            "top-left": (left + margin, top + margin),
        }
        x, y = positions.get(self._position, positions["bottom-right"])
        self._root.geometry(f"+{x}+{y}")
