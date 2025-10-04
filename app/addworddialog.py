# app/AddWordDialog.py
from __future__ import annotations

import tkinter as tk
import tkinter.ttk as ttk
from typing import Callable, List, Optional

from .types_ import WordItem


# ===================== Dialog: Add / Edit =====================
class AddWordDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Widget,
        on_submit: Callable[[WordItem], None],
        initial: Optional[WordItem] = None,
        title: str = "単語追加",
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.on_submit = on_submit
        self.initial = initial or {"word": "", "meaning": "", "genre": ""}
        self._build()
        self.transient(parent)  # stay on top of parent
        self.update_idletasks()
        self._center_over_parent(parent, y_offset=-300)
        self.grab_set()  # modal-like
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build(self) -> None:
        pad = {"padx": 10, "pady": 6}
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # word
        tk.Label(self, text="単語:").grid(row=0, column=0, sticky="nw", **pad)
        wwrap = tk.Frame(self)
        wwrap.grid(row=0, column=1, sticky="nsew", **pad)
        wwrap.columnconfigure(0, weight=1)
        self.e_word = tk.Text(
            wwrap, width=40, height=5, font=("Meiryo", 12), wrap="word"
        )
        self.e_word.grid(row=0, column=0, sticky="nsew")
        sbw = tk.Scrollbar(wwrap, command=self.e_word.yview)
        sbw.grid(row=0, column=1, sticky="ns")
        self.e_word.configure(yscrollcommand=sbw.set)
        self.e_word.insert("1.0", self.initial.get("word", ""))

        # meaning
        tk.Label(self, text="意味:").grid(row=1, column=0, sticky="nw", **pad)
        mwrap = tk.Frame(self)
        mwrap.grid(row=1, column=1, sticky="nsew", **pad)
        mwrap.columnconfigure(0, weight=1)
        self.e_mean = tk.Text(
            mwrap, width=40, height=5, font=("Meiryo", 12), wrap="word"
        )
        self.e_mean.grid(row=0, column=0, sticky="nsew")
        sbm = tk.Scrollbar(mwrap, command=self.e_mean.yview)
        sbm.grid(row=0, column=1, sticky="ns")
        self.e_mean.configure(yscrollcommand=sbm.set)
        self.e_mean.insert("1.0", self.initial.get("meaning", ""))

        # genre
        tk.Label(self, text="ジャンル（例: 食べ物/果物）:").grid(
            row=2, column=0, sticky="w", padx=10, pady=6
        )
        self.e_genre = tk.Entry(self, width=40, font=("Meiryo", 12))
        self.e_genre.grid(row=2, column=1, sticky="ew", ipady=4, padx=10, pady=6)
        self.e_genre.insert(0, self.initial.get("genre", ""))

        # buttons
        btns = tk.Frame(self)
        btns.grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(btns, text="保存", width=10, command=self._submit).pack(
            side="left", padx=6
        )
        tk.Button(btns, text="キャンセル", width=10, command=self._cancel).pack(
            side="left", padx=6
        )

        # keys
        self.bind("<Control-Return>", lambda e: self._submit())
        self.bind("<Control-s>", lambda e: self._submit())
        self.bind("<Escape>", lambda e: self._cancel())
        self.e_word.focus_set()

    def _submit(self) -> None:
        w = self.e_word.get("1.0", "end-1c").strip()
        m = self.e_mean.get("1.0", "end-1c").strip()
        g = self.e_genre.get().strip()
        if self.on_submit and (w or m or g):
            self.on_submit({"word": w, "meaning": m, "genre": g})
        self.destroy()

    def _cancel(self) -> None:
        self.destroy()

    def _center_over_parent(self, parent: tk.Widget, y_offset: int = 0) -> None:
        parent.update_idletasks()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw = parent.winfo_width() or parent.winfo_reqwidth()
        ph = parent.winfo_height() or parent.winfo_reqheight()
        self.update_idletasks()
        dw = self.winfo_width() or self.winfo_reqwidth()
        dh = self.winfo_height() or self.winfo_reqheight()
        x = max(0, px + (pw - dw) // 2)
        y = max(0, py + (ph - dh) // 2 + y_offset)
        self.geometry(f"+{x}+{y}")
