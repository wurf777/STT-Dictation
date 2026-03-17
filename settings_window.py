"""Settings window — tkinter GUI for configuring STT Dictation."""

import tkinter as tk
import threading
import keyboard

import config

# Colors
BG = "#1e1e2e"
FG = "#cdd6f4"
FIELD_BG = "#313244"


class SettingsWindow:
    """Settings window that reuses a single Tk root (never destroyed)."""

    def __init__(self, on_save=None):
        self._on_save = on_save
        self._root = None
        self._thread = None
        self._capturing_hotkey = False
        self._built = False

    def open(self):
        """Open the settings window (non-blocking)."""
        if self._built and self._root:
            # Window already exists — just refresh and show
            self._root.after(0, self._reopen)
            return
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._build_and_run, daemon=True)
        self._thread.start()

    def _reopen(self):
        """Refresh values and show the existing window."""
        self._load_current_values()
        self._root.deiconify()

    def _build_and_run(self):
        root = tk.Tk()
        self._root = root
        root.title("STT Dictation — Inställningar")
        root.resizable(False, False)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        font = ("Segoe UI", 10)
        font_bold = ("Segoe UI", 14, "bold")
        pad = {"padx": 10, "pady": 6}

        # Create variables (with master=root to bind to correct Tcl interpreter)
        self._hotkey_var = tk.StringVar(master=root)
        self._device_var = tk.StringVar(master=root)
        self._output_var = tk.StringVar(master=root)
        self._feedback_var = tk.BooleanVar(master=root)

        # Header
        tk.Label(root, text="Inställningar", font=font_bold, bg=BG, fg=FG).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))

        row = 1

        # ── Hotkey ───────────────────────────────────────────
        tk.Label(root, text="Snabbtangent:", font=font, bg=BG, fg=FG).grid(
            row=row, column=0, sticky="w", **pad)

        hk_frame = tk.Frame(root, bg=BG)
        hk_frame.grid(row=row, column=1, sticky="ew", **pad)

        self._hotkey_label = tk.Label(
            hk_frame, textvariable=self._hotkey_var, font=("Segoe UI", 11, "bold"),
            bg=FIELD_BG, fg=FG, width=12, anchor="center", relief="sunken", padx=5, pady=3)
        self._hotkey_label.pack(side="left", padx=(0, 8))

        self._hotkey_btn = tk.Button(
            hk_frame, text="Ändra...", font=font, command=self._start_hotkey_capture)
        self._hotkey_btn.pack(side="left")
        row += 1

        # ── Audio device ─────────────────────────────────────
        tk.Label(root, text="Mikrofon:", font=font, bg=BG, fg=FG).grid(
            row=row, column=0, sticky="w", **pad)

        self._device_menu_frame = tk.Frame(root, bg=BG)
        self._device_menu_frame.grid(row=row, column=1, sticky="ew", **pad)
        self._build_device_menu()
        row += 1

        # ── Output mode ──────────────────────────────────────
        tk.Label(root, text="Utmatning:", font=font, bg=BG, fg=FG).grid(
            row=row, column=0, sticky="nw", **pad)

        out_frame = tk.Frame(root, bg=BG)
        out_frame.grid(row=row, column=1, sticky="ew", **pad)

        for text, value in [("Klistra in automatiskt (Ctrl+V)", "auto_paste"),
                            ("Bara kopiera till urklipp", "clipboard_only")]:
            tk.Radiobutton(out_frame, text=text,
                            variable=self._output_var, value=value,
                            font=font, bg=BG, fg=FG,
                            selectcolor="#45475a",
                            activebackground=BG, activeforeground=FG).pack(anchor="w")
        row += 1

        # ── Feedback window ──────────────────────────────────
        tk.Label(root, text="Feedback-fönster:", font=font, bg=BG, fg=FG).grid(
            row=row, column=0, sticky="w", **pad)

        tk.Checkbutton(root, text="Visa transkriberings-overlay",
                        variable=self._feedback_var,
                        font=font, bg=BG, fg=FG,
                        selectcolor="#45475a",
                        activebackground=BG, activeforeground=FG).grid(
            row=row, column=1, sticky="w", **pad)
        row += 1

        # ── Buttons ──────────────────────────────────────────
        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(12, 15), padx=10, sticky="e")

        tk.Button(btn_frame, text="Spara", font=font, width=10,
                   command=self._on_save_click).pack(side="right", padx=(5, 0))
        tk.Button(btn_frame, text="Avbryt", font=font, width=10,
                   command=self._on_close).pack(side="right")

        # Load current values
        self._load_current_values()

        # Center on screen
        root.update_idletasks()
        w = root.winfo_width()
        h = root.winfo_height()
        x = (root.winfo_screenwidth() - w) // 2
        y = (root.winfo_screenheight() - h) // 2
        root.geometry(f"+{x}+{y}")

        self._built = True
        root.mainloop()

    def _build_device_menu(self):
        """Build or rebuild the device dropdown."""
        for w in self._device_menu_frame.winfo_children():
            w.destroy()

        font = ("Segoe UI", 10)
        self._devices = config.get_input_devices()
        device_names = ["Standard (systemval)"] + [d["name"] for d in self._devices]

        menu = tk.OptionMenu(self._device_menu_frame, self._device_var, *device_names)
        menu.configure(font=font, bg=FIELD_BG, fg=FG,
                        activebackground="#45475a", activeforeground=FG,
                        highlightthickness=0, width=30)
        menu["menu"].configure(font=font, bg=FIELD_BG, fg=FG,
                                activebackground="#45475a", activeforeground=FG)
        menu.pack(fill="x")

    def _load_current_values(self):
        """Load current config values into the UI variables."""
        self._hotkey_var.set(config.get("hotkey") or "F9")

        cur_device = config.get("audio_device")
        device_name = "Standard (systemval)"
        if cur_device is not None:
            for d in self._devices:
                if d["index"] == cur_device:
                    device_name = d["name"]
                    break
        self._device_var.set(device_name)

        self._output_var.set(config.get("output_mode") or "auto_paste")
        self._feedback_var.set(config.get("show_feedback_window") if config.get("show_feedback_window") is not None else True)

    def _start_hotkey_capture(self):
        """Enter hotkey capture mode — supports single keys and combinations."""
        self._capturing_hotkey = True
        self._hotkey_btn.configure(text="Tryck tangent(er)...")
        self._hotkey_var.set("...")

        def capture():
            # read_hotkey waits for a key combo (e.g. ctrl+shift+f9) or single key
            hotkey = keyboard.read_hotkey(suppress=False)
            if self._capturing_hotkey and self._root:
                self._root.after(0, self._finish_hotkey_capture, hotkey)

        threading.Thread(target=capture, daemon=True).start()

    def _finish_hotkey_capture(self, key_name):
        self._capturing_hotkey = False
        self._hotkey_var.set(key_name)
        self._hotkey_btn.configure(text="Ändra...")

    def _on_save_click(self):
        config.set("hotkey", self._hotkey_var.get())

        selected = self._device_var.get()
        if selected == "Standard (systemval)":
            config.set("audio_device", None)
        else:
            for d in self._devices:
                if d["name"] == selected:
                    config.set("audio_device", d["index"])
                    break

        config.set("output_mode", self._output_var.get())
        config.set("show_feedback_window", self._feedback_var.get())

        config.save()
        print(f"[settings] Sparade: hotkey={config.get('hotkey')}, "
              f"output={config.get('output_mode')}, "
              f"device={config.get('audio_device')}, "
              f"feedback={config.get('show_feedback_window')}")

        if self._on_save:
            self._on_save()

        self._on_close()

    def _on_close(self):
        self._capturing_hotkey = False
        if self._root:
            self._root.withdraw()  # Hide, don't destroy
