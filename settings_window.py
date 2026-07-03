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
        self._beam_var = tk.IntVar(master=root)
        self._repaste_hotkey_var = tk.StringVar(master=root)
        self._correction_hotkey_var = tk.StringVar(master=root)
        self._restore_clipboard_var = tk.BooleanVar(master=root)
        self._post_process_var = tk.BooleanVar(master=root)
        self._learning_var = tk.BooleanVar(master=root)
        self._smart_space_var = tk.BooleanVar(master=root)
        self._smart_period_var = tk.BooleanVar(master=root)
        self._smart_window_var = tk.IntVar(master=root)

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

        tk.Label(root, text="Extra snabbknappar:", font=font, bg=BG, fg=FG).grid(
            row=row, column=0, sticky="nw", **pad)

        extra_hotkey_frame = tk.Frame(root, bg=BG)
        extra_hotkey_frame.grid(row=row, column=1, sticky="ew", **pad)

        tk.Label(extra_hotkey_frame, text="Klistra in senaste", font=font,
                 bg=BG, fg=FG).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 4))
        tk.Entry(extra_hotkey_frame, textvariable=self._repaste_hotkey_var,
                 font=font, bg=FIELD_BG, fg=FG, insertbackground=FG,
                 width=16).grid(row=0, column=1, sticky="w", pady=(0, 4))

        tk.Label(extra_hotkey_frame, text="Korrigera senaste", font=font,
                 bg=BG, fg=FG).grid(row=1, column=0, sticky="w", padx=(0, 8))
        tk.Entry(extra_hotkey_frame, textvariable=self._correction_hotkey_var,
                 font=font, bg=FIELD_BG, fg=FG, insertbackground=FG,
                 width=16).grid(row=1, column=1, sticky="w")
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

        # ── Beam size ────────────────────────────────────────
        tk.Label(root, text="Beam size:", font=font, bg=BG, fg=FG).grid(
            row=row, column=0, sticky="w", **pad)

        beam_frame = tk.Frame(root, bg=BG)
        beam_frame.grid(row=row, column=1, sticky="ew", **pad)

        self._beam_value_label = tk.Label(
            beam_frame, textvariable=self._beam_var, font=("Segoe UI", 11, "bold"),
            bg=FIELD_BG, fg=FG, width=3, anchor="center", relief="sunken")
        self._beam_value_label.pack(side="left", padx=(0, 8))

        tk.Scale(beam_frame, from_=1, to=5, orient="horizontal",
                 variable=self._beam_var, showvalue=False,
                 font=font, bg=BG, fg=FG, troughcolor=FIELD_BG,
                 activebackground="#45475a", highlightthickness=0,
                 length=150).pack(side="left")

        tk.Label(beam_frame, text="(1=snabb, 5=bäst)", font=("Segoe UI", 9),
                 bg=BG, fg="#6c7086").pack(side="left", padx=(8, 0))
        row += 1

        tk.Label(root, text="Textbearbetning:", font=font, bg=BG, fg=FG).grid(
            row=row, column=0, sticky="nw", **pad)

        processing_frame = tk.Frame(root, bg=BG)
        processing_frame.grid(row=row, column=1, sticky="ew", **pad)

        for text, variable in [
            ("Efterprocessa text och kommandon", self._post_process_var),
            ("Logga diktat för inlärning", self._learning_var),
            ("Återställ urklipp efter inklistring", self._restore_clipboard_var),
        ]:
            tk.Checkbutton(processing_frame, text=text,
                           variable=variable,
                           font=font, bg=BG, fg=FG,
                           selectcolor="#45475a",
                           activebackground=BG, activeforeground=FG).pack(anchor="w")
        row += 1

        tk.Label(root, text="Smart fortsättning:", font=font, bg=BG, fg=FG).grid(
            row=row, column=0, sticky="nw", **pad)

        smart_frame = tk.Frame(root, bg=BG)
        smart_frame.grid(row=row, column=1, sticky="ew", **pad)

        tk.Checkbutton(smart_frame, text="Lägg till blanksteg vid fortsättning",
                       variable=self._smart_space_var,
                       font=font, bg=BG, fg=FG,
                       selectcolor="#45475a",
                       activebackground=BG, activeforeground=FG).pack(anchor="w")

        tk.Checkbutton(smart_frame, text="Ta bort föregående punkt vid fortsättning",
                       variable=self._smart_period_var,
                       font=font, bg=BG, fg=FG,
                       selectcolor="#45475a",
                       activebackground=BG, activeforeground=FG).pack(anchor="w")

        smart_window_frame = tk.Frame(smart_frame, bg=BG)
        smart_window_frame.pack(anchor="w", pady=(4, 0))
        tk.Label(smart_window_frame, text="Tidsfönster:", font=font,
                 bg=BG, fg=FG).pack(side="left", padx=(0, 8))
        tk.Spinbox(smart_window_frame, from_=5, to=600, increment=5,
                   textvariable=self._smart_window_var, font=font,
                   bg=FIELD_BG, fg=FG, insertbackground=FG,
                   width=6).pack(side="left")
        tk.Label(smart_window_frame, text="sekunder", font=("Segoe UI", 9),
                 bg=BG, fg="#6c7086").pack(side="left", padx=(8, 0))
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
        self._beam_var.set(config.get("beam_size") or 5)
        self._repaste_hotkey_var.set(config.get("repaste_hotkey") or "")
        self._correction_hotkey_var.set(config.get("correction_hotkey") or "")
        self._restore_clipboard_var.set(bool(config.get("restore_clipboard_after_paste")))
        self._post_process_var.set(bool(config.get("post_process_enabled")))
        self._learning_var.set(bool(config.get("dictation_learning_enabled")))
        self._smart_space_var.set(bool(config.get("smart_leading_space_enabled")))
        self._smart_period_var.set(bool(config.get("smart_remove_previous_period_enabled")))
        self._smart_window_var.set(config.get("smart_leading_space_window_seconds") or 90)

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
        config.set("beam_size", self._beam_var.get())
        config.set("repaste_hotkey", self._repaste_hotkey_var.get().strip())
        config.set("correction_hotkey", self._correction_hotkey_var.get().strip())
        config.set("restore_clipboard_after_paste", self._restore_clipboard_var.get())
        config.set("post_process_enabled", self._post_process_var.get())
        config.set("dictation_learning_enabled", self._learning_var.get())
        config.set("smart_leading_space_enabled", self._smart_space_var.get())
        config.set("smart_remove_previous_period_enabled", self._smart_period_var.get())
        config.set("smart_leading_space_window_seconds", self._smart_window_seconds())

        config.save()
        print(f"[settings] Sparade: hotkey={config.get('hotkey')}, "
              f"output={config.get('output_mode')}, "
              f"device={config.get('audio_device')}, "
              f"feedback={config.get('show_feedback_window')}, "
              f"beam_size={config.get('beam_size')}, "
              f"repaste_hotkey={config.get('repaste_hotkey')}, "
              f"correction_hotkey={config.get('correction_hotkey')}, "
              f"smart_space={config.get('smart_leading_space_enabled')}, "
              f"smart_period={config.get('smart_remove_previous_period_enabled')}")

        if self._on_save:
            self._on_save()

        self._on_close()

    def _on_close(self):
        self._capturing_hotkey = False
        if self._root:
            self._root.withdraw()  # Hide, don't destroy

    def _smart_window_seconds(self):
        try:
            value = int(self._smart_window_var.get())
        except (tk.TclError, ValueError):
            value = 90
        return max(5, min(600, value))
