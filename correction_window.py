"""Window for correcting the latest dictation and saving a learning example."""

import threading
import tkinter as tk
from tkinter import ttk

from learning_suggestions import (
    add_to_learning_basket,
    approve_replacement,
    find_text_changes,
    suggest_replacements,
)


BG = "#1e1e2e"
FG = "#cdd6f4"
FIELD_BG = "#313244"
MUTED = "#a6adc8"
ACCENT = "#45475a"


class CorrectionWindow:
    """Correction editor with simple learning-rule suggestions."""

    def __init__(self, get_record, on_save, on_paste=None):
        self._get_record = get_record
        self._on_save = on_save
        self._on_paste = on_paste
        self._root = None
        self._thread = None
        self._built = False
        self._record = None
        self._suggestions = []
        self._refresh_after_id = None

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
        root.geometry("840x820")
        root.minsize(720, 700)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        font = ("Segoe UI", 10)
        font_bold = ("Segoe UI", 12, "bold")

        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(2, weight=0)
        root.grid_rowconfigure(4, weight=1)
        root.grid_rowconfigure(6, weight=0, minsize=96)
        root.grid_rowconfigure(9, weight=0, minsize=130)

        tk.Label(root, text="Rå Whisper-text", font=font_bold, bg=BG, fg=FG).grid(
            row=0, column=0, sticky="w", padx=12, pady=(12, 4)
        )
        self._raw_text = tk.Text(
            root,
            height=4,
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
            height=9,
            wrap="word",
            font=font,
            bg=FIELD_BG,
            fg=FG,
            insertbackground=FG,
            relief="flat",
        )
        self._corrected_text.grid(row=4, column=0, sticky="nsew", padx=12)
        self._corrected_text.bind("<<Modified>>", self._on_corrected_modified)

        tk.Label(root, text="Ändringar", font=font_bold, bg=BG, fg=FG).grid(
            row=5, column=0, sticky="w", padx=12, pady=(12, 4)
        )
        self._diff_text = tk.Text(
            root,
            height=4,
            wrap="word",
            font=("Consolas", 9),
            bg=FIELD_BG,
            fg=MUTED,
            insertbackground=FG,
            relief="flat",
        )
        self._diff_text.grid(row=6, column=0, sticky="nsew", padx=12)

        tk.Label(root, text="Förslag till ordlistan", font=font_bold, bg=BG, fg=FG).grid(
            row=7, column=0, sticky="w", padx=12, pady=(12, 2)
        )
        self._suggestion_hint_var = tk.StringVar(master=root)
        tk.Label(
            root,
            textvariable=self._suggestion_hint_var,
            font=font,
            bg=BG,
            fg=MUTED,
            wraplength=780,
            justify="left",
        ).grid(row=8, column=0, sticky="w", padx=12, pady=(0, 4))

        suggestions_frame = tk.Frame(root, bg=BG)
        suggestions_frame.grid(row=9, column=0, sticky="nsew", padx=12)
        suggestions_frame.grid_columnconfigure(0, weight=1)
        suggestions_frame.grid_rowconfigure(0, weight=1, minsize=86)

        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure(
            "Learning.Treeview",
            background=FIELD_BG,
            foreground=FG,
            fieldbackground=FIELD_BG,
            borderwidth=0,
            rowheight=24,
            font=font,
        )
        style.configure(
            "Learning.Treeview.Heading",
            background=ACCENT,
            foreground=FG,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        style.map("Learning.Treeview", background=[("selected", ACCENT)])

        self._suggestion_tree = ttk.Treeview(
            suggestions_frame,
            columns=("from", "to"),
            show="headings",
            height=4,
            style="Learning.Treeview",
            selectmode="browse",
        )
        self._suggestion_tree.heading("from", text="När appen hör")
        self._suggestion_tree.heading("to", text="Skriv istället")
        self._suggestion_tree.column("from", width=300, anchor="w")
        self._suggestion_tree.column("to", width=300, anchor="w")
        self._suggestion_tree.grid(row=0, column=0, sticky="nsew")

        suggestion_scroll = tk.Scrollbar(
            suggestions_frame, command=self._suggestion_tree.yview
        )
        suggestion_scroll.grid(row=0, column=1, sticky="ns")
        self._suggestion_tree.configure(yscrollcommand=suggestion_scroll.set)

        suggestion_buttons = tk.Frame(suggestions_frame, bg=BG)
        suggestion_buttons.grid(row=1, column=0, columnspan=2, sticky="e", pady=(6, 0))
        tk.Button(
            suggestion_buttons,
            text="Godkänn markerad",
            font=font,
            command=self._approve_selected_suggestion,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            suggestion_buttons,
            text="Godkänn alla",
            font=font,
            command=self._approve_all_suggestions,
        ).pack(side="right")
        tk.Button(
            suggestion_buttons,
            text="Lägg markerad i korg",
            font=font,
            command=self._basket_selected_suggestion,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            suggestion_buttons,
            text="Lägg alla i korg",
            font=font,
            command=self._basket_all_suggestions,
        ).pack(side="right")

        self._status_var = tk.StringVar(master=root)
        tk.Label(root, textvariable=self._status_var, font=font, bg=BG, fg=MUTED).grid(
            row=10, column=0, sticky="w", padx=12, pady=(8, 0)
        )

        buttons = tk.Frame(root, bg=BG)
        buttons.grid(row=11, column=0, sticky="e", padx=12, pady=12)
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
        self._diff_text.configure(state="normal")
        self._diff_text.delete("1.0", "end")
        self._diff_text.configure(state="disabled")
        self._clear_suggestions()

        if not self._record:
            self._raw_text.insert("1.0", "Inget diktat finns ännu.")
            self._raw_text.configure(state="disabled")
            self._suggestion_hint_var.set("")
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
        self._corrected_text.edit_modified(False)
        self._refresh_diff(raw_text, processed_text)
        self._refresh_suggestions(raw_text, processed_text)
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
            self._refresh_diff(self._record.get("raw_text") or "", corrected)
            self._refresh_suggestions(self._record.get("raw_text") or "", corrected)
            if self._suggestions:
                self._status_var.set(
                    "Sparat. Jag hittade förslag som du kan godkänna eller lägga i korgen."
                )
            else:
                self._status_var.set("Sparat. Ingen säker regel hittades automatiskt.")
            if close_on_success and not self._suggestions:
                self._on_close()
            return corrected

        self._status_var.set("Kunde inte spara korrigeringen.")
        return None

    def _refresh_suggestions(self, raw_text, corrected_text):
        self._clear_suggestions()
        self._suggestions = suggest_replacements(raw_text, corrected_text)
        for suggestion in self._suggestions:
            self._suggestion_tree.insert(
                "",
                tk.END,
                values=(suggestion["from"], suggestion["to"]),
            )
        self._update_suggestion_hint(raw_text, corrected_text)

    def _on_corrected_modified(self, event=None):
        if not self._corrected_text.edit_modified():
            return
        self._corrected_text.edit_modified(False)
        if self._refresh_after_id:
            self._root.after_cancel(self._refresh_after_id)
        self._refresh_after_id = self._root.after(250, self._refresh_from_editor)

    def _refresh_from_editor(self):
        self._refresh_after_id = None
        if not self._record:
            return

        raw_text = self._record.get("raw_text") or ""
        corrected_text = self._corrected_text.get("1.0", "end").strip()
        self._refresh_diff(raw_text, corrected_text)
        self._refresh_suggestions(raw_text, corrected_text)

    def _refresh_diff(self, raw_text, corrected_text):
        diff_lines = _format_diff(raw_text, corrected_text)
        self._diff_text.configure(state="normal")
        self._diff_text.delete("1.0", "end")
        self._diff_text.insert("1.0", "\n".join(diff_lines))
        self._diff_text.configure(state="disabled")

    def _update_suggestion_hint(self, raw_text, corrected_text):
        raw = (raw_text or "").strip()
        corrected = (corrected_text or "").strip()
        if not raw and not corrected:
            self._suggestion_hint_var.set("")
        elif raw == corrected:
            self._suggestion_hint_var.set(
                "Ingen skillnad hittades. Ändra facittexten först, så kan appen föreslå vad den borde lära sig."
            )
        elif self._suggestions:
            self._suggestion_hint_var.set(
                "Appen hittade konkreta skillnader. Godkänn dem direkt eller lägg dem i lärandekorgen för senare genomgång."
            )
        else:
            self._suggestion_hint_var.set(
                "Facit skiljer sig från råtexten, men skillnaden är för osäker för en automatisk regel. Den är ändå sparad i historiken."
            )

    def _clear_suggestions(self):
        self._suggestions = []
        if hasattr(self, "_suggestion_tree"):
            for item in self._suggestion_tree.get_children():
                self._suggestion_tree.delete(item)

    def _approve_selected_suggestion(self):
        selection = self._suggestion_tree.selection()
        if not selection:
            self._status_var.set("Markera ett förslag först.")
            return
        self._approve_items(selection)

    def _approve_all_suggestions(self):
        items = self._suggestion_tree.get_children()
        if not items:
            self._status_var.set("Inga förslag att godkänna.")
            return
        self._approve_items(items)

    def _basket_selected_suggestion(self):
        selection = self._suggestion_tree.selection()
        if not selection:
            self._status_var.set("Markera ett förslag först.")
            return
        self._basket_items(selection)

    def _basket_all_suggestions(self):
        items = self._suggestion_tree.get_children()
        if not items:
            self._status_var.set("Inga förslag att lägga i korgen.")
            return
        self._basket_items(items)

    def _approve_items(self, items):
        approved = 0
        for item in list(items):
            src, dst = self._suggestion_tree.item(item)["values"]
            if approve_replacement(str(src), str(dst)):
                approved += 1
                self._suggestion_tree.delete(item)

        self._suggestions = [
            {
                "from": self._suggestion_tree.item(item)["values"][0],
                "to": self._suggestion_tree.item(item)["values"][1],
            }
            for item in self._suggestion_tree.get_children()
        ]
        if approved:
            self._status_var.set(f"Godkände {approved} regel/regler till ordlistan.")
        else:
            self._status_var.set("Ingen regel sparades.")

    def _basket_items(self, items):
        saved = 0
        raw_text = self._record.get("raw_text") if self._record else ""
        corrected_text = self._corrected_text.get("1.0", "end").strip()
        record_id = self._record.get("id") if self._record else None
        for item in list(items):
            src, dst = self._suggestion_tree.item(item)["values"]
            suggestion = {"from": str(src), "to": str(dst)}
            if add_to_learning_basket(
                suggestion,
                raw_text=raw_text or "",
                corrected_text=corrected_text,
                record_id=record_id,
            ):
                saved += 1

        if saved:
            self._status_var.set(f"Lade {saved} förslag i lärandekorgen.")
        else:
            self._status_var.set("Inget förslag lades i korgen.")

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


def _format_diff(raw_text, corrected_text):
    raw = (raw_text or "").strip()
    corrected = (corrected_text or "").strip()
    if not raw and not corrected:
        return []
    if raw == corrected:
        return ["Ingen skillnad mellan råtext och facit ännu."]

    changes = find_text_changes(raw, corrected)
    if not changes:
        return ["Ingen tydlig ordskillnad hittades."]

    lines = []
    for change in changes[:12]:
        if change["from"]:
            lines.append(f"- {change['from']}")
        if change["to"]:
            lines.append(f"+ {change['to']}")
    if len(changes) > 12:
        lines.append(f"... {len(changes) - 12} ändring(ar) till")
    return lines[:80]
