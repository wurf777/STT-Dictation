"""Vocabulary window — manage custom names/words and post-processing replacements."""

import tkinter as tk
from tkinter import ttk, messagebox
import threading

import config

# Colors (match settings_window.py)
BG = "#1e1e2e"
FG = "#cdd6f4"
FIELD_BG = "#313244"
MUTED = "#6c7086"
ACCENT = "#45475a"


class VocabularyWindow:
    """Window for managing vocabulary (initial_prompt) and text replacements."""

    def __init__(self, on_save=None):
        self._on_save = on_save
        self._root = None
        self._thread = None
        self._built = False

    def open(self):
        """Open the vocabulary window (non-blocking)."""
        if self._built and self._root:
            self._root.after(0, self._reopen)
            return
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._build_and_run, daemon=True)
        self._thread.start()

    def _reopen(self):
        self._load_current_values()
        self._root.deiconify()

    def _build_and_run(self):
        root = tk.Tk()
        self._root = root
        root.title("STT Dictation — Ordlista")
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        font = ("Segoe UI", 10)
        font_bold = ("Segoe UI", 14, "bold")
        font_section = ("Segoe UI", 11, "bold")

        # Header
        tk.Label(root, text="Ordlista & ersättningar", font=font_bold,
                 bg=BG, fg=FG).pack(anchor="w", padx=15, pady=(15, 4))
        tk.Label(root,
                 text="Lär Whisper hur namn och speciella ord ska skrivas.",
                 font=("Segoe UI", 9), bg=BG, fg=MUTED).pack(anchor="w", padx=15, pady=(0, 10))

        # ── Section 1: Vocabulary (initial_prompt) ───────────
        vocab_frame = tk.LabelFrame(
            root, text=" Namn & ord (nudgar modellen) ",
            font=font_section, bg=BG, fg=FG, bd=1, relief="groove", padx=10, pady=8)
        vocab_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        tk.Label(vocab_frame,
                 text="Lägg till namn/ord som modellen ska försöka känna igen.\n"
                      "Tips: skriv med rätt stavning och versalisering.",
                 font=("Segoe UI", 9), bg=BG, fg=MUTED, justify="left").pack(anchor="w", pady=(0, 6))

        vocab_list_frame = tk.Frame(vocab_frame, bg=BG)
        vocab_list_frame.pack(fill="both", expand=True)

        self._vocab_list = tk.Listbox(
            vocab_list_frame, height=7, bg=FIELD_BG, fg=FG,
            selectbackground=ACCENT, selectforeground=FG,
            highlightthickness=0, bd=0, font=font, activestyle="none")
        self._vocab_list.pack(side="left", fill="both", expand=True)

        vocab_scroll = tk.Scrollbar(vocab_list_frame, command=self._vocab_list.yview)
        vocab_scroll.pack(side="right", fill="y")
        self._vocab_list.configure(yscrollcommand=vocab_scroll.set)

        vocab_input_frame = tk.Frame(vocab_frame, bg=BG)
        vocab_input_frame.pack(fill="x", pady=(6, 0))

        self._vocab_entry = tk.Entry(
            vocab_input_frame, font=font, bg=FIELD_BG, fg=FG,
            insertbackground=FG, bd=0, highlightthickness=1,
            highlightbackground=ACCENT, highlightcolor=FG)
        self._vocab_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self._vocab_entry.bind("<Return>", lambda e: self._add_vocab())

        tk.Button(vocab_input_frame, text="Lägg till", font=font, width=10,
                  command=self._add_vocab).pack(side="left", padx=(6, 0))
        tk.Button(vocab_input_frame, text="Ta bort", font=font, width=10,
                  command=self._remove_vocab).pack(side="left", padx=(6, 0))

        # ── Section 2: Replacements ──────────────────────────
        repl_frame = tk.LabelFrame(
            root, text=" Ersättningar (efterbehandling) ",
            font=font_section, bg=BG, fg=FG, bd=1, relief="groove", padx=10, pady=8)
        repl_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        tk.Label(repl_frame,
                 text="Byt ut feltranskriberade ord mot rätt stavning.\n"
                      "Matchar hela ord, skiftlägesokänsligt.",
                 font=("Segoe UI", 9), bg=BG, fg=MUTED, justify="left").pack(anchor="w", pady=(0, 6))

        # Treeview styling
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("Vocab.Treeview", background=FIELD_BG, foreground=FG,
                        fieldbackground=FIELD_BG, bordercolor=ACCENT, borderwidth=0,
                        rowheight=24, font=font)
        style.configure("Vocab.Treeview.Heading", background=ACCENT, foreground=FG,
                        font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Vocab.Treeview", background=[("selected", ACCENT)],
                  foreground=[("selected", FG)])

        repl_list_frame = tk.Frame(repl_frame, bg=BG)
        repl_list_frame.pack(fill="both", expand=True)

        self._repl_tree = ttk.Treeview(
            repl_list_frame, columns=("from", "to"), show="headings",
            height=6, style="Vocab.Treeview", selectmode="browse")
        self._repl_tree.heading("from", text="Från")
        self._repl_tree.heading("to", text="Till")
        self._repl_tree.column("from", width=200, anchor="w")
        self._repl_tree.column("to", width=200, anchor="w")
        self._repl_tree.pack(side="left", fill="both", expand=True)

        repl_scroll = tk.Scrollbar(repl_list_frame, command=self._repl_tree.yview)
        repl_scroll.pack(side="right", fill="y")
        self._repl_tree.configure(yscrollcommand=repl_scroll.set)

        repl_input_frame = tk.Frame(repl_frame, bg=BG)
        repl_input_frame.pack(fill="x", pady=(6, 0))

        self._repl_from = tk.Entry(
            repl_input_frame, font=font, bg=FIELD_BG, fg=FG,
            insertbackground=FG, bd=0, highlightthickness=1,
            highlightbackground=ACCENT, highlightcolor=FG)
        self._repl_from.pack(side="left", fill="x", expand=True, ipady=3)

        tk.Label(repl_input_frame, text="→", font=font_bold,
                 bg=BG, fg=MUTED).pack(side="left", padx=8)

        self._repl_to = tk.Entry(
            repl_input_frame, font=font, bg=FIELD_BG, fg=FG,
            insertbackground=FG, bd=0, highlightthickness=1,
            highlightbackground=ACCENT, highlightcolor=FG)
        self._repl_to.pack(side="left", fill="x", expand=True, ipady=3)
        self._repl_to.bind("<Return>", lambda e: self._add_replacement())

        repl_btn_frame = tk.Frame(repl_frame, bg=BG)
        repl_btn_frame.pack(fill="x", pady=(6, 0))

        tk.Button(repl_btn_frame, text="Lägg till", font=font, width=10,
                  command=self._add_replacement).pack(side="left")
        tk.Button(repl_btn_frame, text="Ta bort", font=font, width=10,
                  command=self._remove_replacement).pack(side="left", padx=(6, 0))

        # ── Save / Cancel ────────────────────────────────────
        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        tk.Button(btn_frame, text="Spara", font=font, width=10,
                  command=self._on_save_click).pack(side="right", padx=(5, 0))
        tk.Button(btn_frame, text="Avbryt", font=font, width=10,
                  command=self._on_close).pack(side="right")

        self._load_current_values()

        # Size & center
        root.update_idletasks()
        w = max(root.winfo_reqwidth(), 520)
        h = max(root.winfo_reqheight(), 560)
        x = (root.winfo_screenwidth() - w) // 2
        y = (root.winfo_screenheight() - h) // 2
        root.geometry(f"{w}x{h}+{x}+{y}")
        root.minsize(520, 520)

        self._built = True
        root.mainloop()

    # ── Vocab handlers ─────────────────────────────────────────
    def _add_vocab(self):
        word = self._vocab_entry.get().strip()
        if not word:
            return
        existing = [self._vocab_list.get(i) for i in range(self._vocab_list.size())]
        if word.lower() in [w.lower() for w in existing]:
            self._vocab_entry.delete(0, tk.END)
            return
        self._vocab_list.insert(tk.END, word)
        self._vocab_entry.delete(0, tk.END)

    def _remove_vocab(self):
        sel = self._vocab_list.curselection()
        if sel:
            self._vocab_list.delete(sel[0])

    # ── Replacement handlers ───────────────────────────────────
    def _add_replacement(self):
        src = self._repl_from.get().strip()
        dst = self._repl_to.get().strip()
        if not src:
            return
        # Remove any existing row with same "from" (case-insensitive)
        for item in self._repl_tree.get_children():
            if self._repl_tree.item(item)["values"][0].lower() == src.lower():
                self._repl_tree.delete(item)
        self._repl_tree.insert("", tk.END, values=(src, dst))
        self._repl_from.delete(0, tk.END)
        self._repl_to.delete(0, tk.END)
        self._repl_from.focus_set()

    def _remove_replacement(self):
        sel = self._repl_tree.selection()
        if sel:
            self._repl_tree.delete(sel[0])

    # ── Load / Save ────────────────────────────────────────────
    def _load_current_values(self):
        self._vocab_list.delete(0, tk.END)
        for word in config.get("vocabulary") or []:
            if isinstance(word, str) and word.strip():
                self._vocab_list.insert(tk.END, word.strip())

        for item in self._repl_tree.get_children():
            self._repl_tree.delete(item)
        replacements = config.get("replacements") or {}
        for src, dst in replacements.items():
            self._repl_tree.insert("", tk.END, values=(src, dst))

    def _on_save_click(self):
        vocab = [self._vocab_list.get(i) for i in range(self._vocab_list.size())]

        replacements = {}
        for item in self._repl_tree.get_children():
            src, dst = self._repl_tree.item(item)["values"]
            src = str(src).strip()
            dst = str(dst).strip()
            if src:
                replacements[src] = dst

        config.set("vocabulary", vocab)
        config.set("replacements", replacements)
        config.save()
        print(f"[vocab] Sparade: {len(vocab)} ord, {len(replacements)} ersättningar")

        if self._on_save:
            self._on_save()

        self._on_close()

    def _on_close(self):
        if self._root:
            self._root.withdraw()
