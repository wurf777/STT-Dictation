"""Window for correcting the latest dictation and saving a learning example."""

import threading
import tkinter as tk


BG = "#1e1e2e"
FG = "#cdd6f4"
FIELD_BG = "#313244"
MUTED = "#a6adc8"


class CorrectionWindow:
    """Tiny correction editor that can be reopened for new dictations."""

    def __init__(self, get_record, on_save, on_paste=None):
        self._get_record = get_record
        self._on_save = on_save
        self._on_paste = on_paste
        self._root = None
        self._thread = None
        self._built = False
        self._record = None

    def open(self):
        if self._built and self._root:
            self._root.after(0, self._reopen)
            return
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._build_and_run, daemon=True)
        self._thread.start()

    def _build_and_run(self):
        root = tk.Tk()
        self._root = root
        root.title("STT Dictation - Korrigera senaste diktat")
        root.geometry("720x520")
        root.minsize(560, 420)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        font = ("Segoe UI", 10)
        font_bold = ("Segoe UI", 12, "bold")

        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(2, weight=1)
        root.grid_rowconfigure(4, weight=2)

        tk.Label(root, text="Rå Whisper-text", font=font_bold, bg=BG, fg=FG).grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 4)
        )
        self._raw_text = tk.Text(
            root,
            height=5,
            wrap="word",
            font=font,
            bg=FIELD_BG,
            fg=MUTED,
            insertbackground=FG,
            relief="flat",
        )
        self._raw_text.grid(row=1, column=0, sticky="nsew", padx=12)

        tk.Label(root, text="Så här skulle det ha blivit", font=font_bold, bg=BG, fg=FG).grid(
            row=3, column=0, sticky="w", padx=12, pady=(12, 4)
        )
        self._corrected_text = tk.Text(
            root,
            wrap="word",
            font=font,
            bg=FIELD_BG,
            fg=FG,
            insertbackground=FG,
            relief="flat",
        )
        self._corrected_text.grid(row=4, column=0, sticky="nsew", padx=12)

        self._status_var = tk.StringVar(master=root)
        tk.Label(root, textvariable=self._status_var, font=font, bg=BG, fg=MUTED).grid(
            row=5, column=0, sticky="w", padx=12, pady=(8, 0)
        )

        buttons = tk.Frame(root, bg=BG)
        buttons.grid(row=6, column=0, sticky="e", padx=12, pady=12)
        tk.Button(
            buttons,
            text="Spara och klistra in",
            font=font,
            command=self._save_and_paste,
        ).pack(side="right", padx=(8, 0))
        tk.Button(buttons, text="Spara facit", font=font, command=self._save).pack(
            side="right", padx=(8, 0)
        )
        tk.Button(buttons, text="Stäng", font=font, command=self._on_close).pack(
            side="right"
        )

        self._built = True
        self._load_record()
        root.mainloop()

    def _reopen(self):
        self._load_record()
        self._root.deiconify()
        self._focus_window()

    def _load_record(self):
        self._record = self._get_record()
        self._raw_text.configure(state="normal")
        self._raw_text.delete("1.0", "end")
        self._corrected_text.delete("1.0", "end")

        if not self._record:
            self._raw_text.insert("1.0", "Inget diktat finns ännu.")
            self._raw_text.configure(state="disabled")
            self._status_var.set("")
            return

        raw_text = self._record.get("raw_text") or ""
        processed_text = (
            self._record.get("corrected_text")
            or self._record.get("processed_text")
            or self._record.get("output_text")
            or ""
        )

        self._raw_text.insert("1.0", raw_text)
        self._raw_text.configure(state="disabled")
        self._corrected_text.insert("1.0", processed_text)
        self._status_var.set("Redigera texten och spara när den stämmer.")
        self._corrected_text.focus_set()
        self._focus_window()

    def _save(self):
        self._save_current(close_on_success=True)

    def _save_and_paste(self):
        corrected = self._save_current(close_on_success=False)
        if corrected and self._on_paste:
            self._on_close()
            self._on_paste(corrected)

    def _save_current(self, close_on_success):
        if not self._record:
            self._status_var.set("Inget diktat att korrigera.")
            return None

        corrected = self._corrected_text.get("1.0", "end").strip()
        if self._on_save(corrected, self._record.get("id")):
            self._status_var.set("Sparat.")
            if close_on_success:
                self._on_close()
            return corrected
        else:
            self._status_var.set("Kunde inte spara korrigeringen.")
            return None

    def _on_close(self):
        if self._root:
            self._root.withdraw()

    def _focus_window(self):
        if not self._root:
            return

        self._root.lift()
        self._root.attributes("-topmost", True)
        self._root.after(250, lambda: self._root.attributes("-topmost", False))
        self._root.focus_force()
