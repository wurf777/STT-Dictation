"""STT Dictation — Push-to-talk dictation tool for Windows.

Hold F9 to record, release to transcribe and paste.
Runs as a system tray application.
"""

import sys
import threading

from recorder import Recorder
from transcriber import Transcriber
from hotkey_manager import HotkeyManager
from output_handler import output_text
from feedback_window import FeedbackWindow
from tray import TrayIcon
from settings_window import SettingsWindow
import config


class App:
    def __init__(self):
        self.recorder = Recorder()
        self.transcriber = Transcriber()
        self.feedback = FeedbackWindow() if config.get("show_feedback_window") else None
        self.tray = TrayIcon(on_exit=self.shutdown, on_settings=self.open_settings)
        self.hotkey = HotkeyManager(
            on_press=self.on_hotkey_press,
            on_release=self.on_hotkey_release,
            hotkey=config.get("hotkey"),
        )
        self.settings_window = SettingsWindow(on_save=self._apply_settings)
        self._audio_device = config.get("audio_device")
        self._transcribe_lock = threading.Lock()

    def run(self):
        """Start all components and run the app."""
        # Load model (takes a moment)
        print("[app] Laddar Whisper-modell...")
        self.transcriber.load_model()

        # Start feedback window thread
        if self.feedback:
            self.feedback.start()

        # Start hotkey listener
        self.hotkey.start()

        print("[app] Redo! Håll F9 för att diktera.")

        # Run tray icon on main thread (blocking)
        self.tray.start()

    def on_hotkey_press(self):
        """Called when the hotkey is pressed — start recording."""
        try:
            self.recorder.start(device=self._get_audio_device())
            self.tray.update_title("STT Dictation — 🎙 Spelar in...")
            if self.feedback:
                self.feedback.show("🎙 Spelar in...")
        except Exception as e:
            print(f"[app] Inspelning kunde inte startas: {e}")
            if self.feedback:
                self.feedback.show(f"❌ Mikrofon-fel: {e}")
                self.feedback.hide_after_delay(3000)

    def _get_audio_device(self):
        """Return configured audio device index, or None for default."""
        return getattr(self, '_audio_device', None)

    def on_hotkey_release(self):
        """Called when the hotkey is released — stop and transcribe."""
        audio = self.recorder.stop()
        duration = len(audio) / self.recorder.sample_rate

        if duration < 0.3:
            if self.feedback:
                self.feedback.hide()
            self.tray.update_title("STT Dictation — Redo")
            return

        if self.feedback:
            self.feedback.update_text("⏳ Transkriberar...")
        self.tray.update_title("STT Dictation — Transkriberar...")

        # Transcribe in a separate thread to avoid blocking the hotkey listener
        threading.Thread(target=self._transcribe_and_output, args=(audio,), daemon=True).start()

    def _transcribe_and_output(self, audio):
        with self._transcribe_lock:
            try:
                text = self.transcriber.transcribe(audio)
                if text:
                    output_text(text)
                    if self.feedback:
                        self.feedback.update_text(text)
                        self.feedback.hide_after_delay()
                else:
                    if self.feedback:
                        self.feedback.hide()
            except Exception as e:
                print(f"[app] Transkribering misslyckades: {e}")
                if self.feedback:
                    self.feedback.update_text(f"❌ Fel: {e}")
                    self.feedback.hide_after_delay(3000)
            finally:
                self.tray.update_title("STT Dictation — Redo")

    def open_settings(self):
        """Open the settings window."""
        self.settings_window.open()

    def _apply_settings(self):
        """Called when settings are saved — apply changes live."""
        # Update audio device
        self._audio_device = config.get("audio_device")

        # Update output mode (read at paste-time from config, no action needed)

        # Re-bind hotkey if changed
        new_hotkey = config.get("hotkey")
        if new_hotkey != self.hotkey.hotkey:
            self.hotkey.stop()
            self.hotkey = HotkeyManager(
                on_press=self.on_hotkey_press,
                on_release=self.on_hotkey_release,
                hotkey=new_hotkey,
            )
            self.hotkey.start()

        # Toggle feedback window
        if config.get("show_feedback_window") and not self.feedback:
            self.feedback = FeedbackWindow()
            self.feedback.start()
        elif not config.get("show_feedback_window") and self.feedback:
            self.feedback.shutdown()
            self.feedback = None

        print(f"[app] Inställningar uppdaterade (hotkey={config.get('hotkey')}, "
              f"enhet={config.get('audio_device')}, utmatning={config.get('output_mode')})")

    def shutdown(self):
        """Clean up and exit."""
        print("[app] Avslutar...")
        self.hotkey.stop()
        if self.feedback:
            self.feedback.shutdown()
        self.tray.stop()


def cli_test():
    """Simple CLI loop for testing recording + transcription."""
    transcriber = Transcriber()

    print("Startar STT Dictation (CLI-testläge)")
    print("=" * 40)
    transcriber.load_model()
    print()

    recorder = Recorder()

    while True:
        try:
            input("Tryck Enter för att börja spela in (Ctrl+C för att avsluta)...")
            recorder.start()
            print("🎙  Spelar in — tryck Enter för att stoppa...")
            input()
            audio = recorder.stop()

            duration = len(audio) / recorder.sample_rate
            print(f"Inspelat: {duration:.1f}s")

            if duration < 0.3:
                print("För kort inspelning, hoppar över.\n")
                continue

            print("Transkriberar...")
            text = transcriber.transcribe(audio)
            print(f"\n>>> {text}\n")

        except KeyboardInterrupt:
            print("\nAvslutar.")
            break


if __name__ == "__main__":
    if "--cli" in sys.argv:
        cli_test()
    else:
        app = App()
        app.run()
