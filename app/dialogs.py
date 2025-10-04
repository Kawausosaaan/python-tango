# app/dialogs.py
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


# ===================== Window: List =====================
class WordListWindow(tk.Toplevel):
    """List/edit/delete words.
    - Double click / Enter / F2: edit
    - Delete / Backspace: delete selected
    - on_changed: notify caller to save/rebuild tree/order
    """

    def __init__(
        self,
        parent: tk.Widget,
        words_ref: List[WordItem],
        on_changed: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)
        self.title("単語一覧")
        self.geometry("720x440")
        self.words_ref = words_ref
        self.on_changed = on_changed
        self._build()
        self.refresh()

    def _build(self) -> None:
        bar = tk.Frame(self)
        bar.pack(side="top", fill="x", pady=(8, 4))
        tk.Label(bar, text="（ダブルクリックで編集 / Deleteで削除）").pack(
            side="left", padx=12
        )

        body = tk.Frame(self)
        body.pack(side="top", fill="both", expand=True)

        columns = ("word", "meaning", "genre")
        self.tree = ttk.Treeview(
            body, columns=columns, show="headings", height=16, selectmode="extended"
        )
        for cid, text, w in (
            ("word", "単語", 220),
            ("meaning", "意味", 360),
            ("genre", "ジャンル", 120),
        ):
            self.tree.heading(cid, text=text)
            self.tree.column(cid, width=w, anchor="w")

        vsb = tk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.bind("<Delete>", self._on_delete)
        self.tree.bind("<BackSpace>", self._on_delete)
        self.tree.bind("<Double-1>", self._on_edit)
        self.tree.bind("<Return>", self._on_edit)
        self.tree.bind("<F2>", self._on_edit)

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, item in enumerate(self.words_ref):
            self.tree.insert(
                "",
                "end",
                iid=f"row-{i}",
                values=(
                    item.get("word", ""),
                    item.get("meaning", ""),
                    item.get("genre", ""),
                ),
            )

    def _selected_indices(self) -> List[int]:
        out: List[int] = []
        for iid in self.tree.selection():
            try:
                out.append(int(iid.split("-")[1]))
            except Exception:
                pass
        return out

    def _on_edit(self, _evt=None) -> None:
        idxs = self._selected_indices()
        if not idxs:
            return
        idx = idxs[0]
        if not (0 <= idx < len(self.words_ref)):
            return
        current = dict(self.words_ref[idx])

        def on_submit(updated: WordItem) -> None:
            self.words_ref[idx] = {
                "word": updated.get("word", ""),
                "meaning": updated.get("meaning", ""),
                "genre": updated.get("genre", ""),
            }
            self.refresh()
            if self.on_changed:
                self.on_changed()

        AddWordDialog(self, on_submit=on_submit, initial=current, title="単語を編集")

    def _on_delete(self, _evt=None) -> None:
        idxs = self._selected_indices()
        if not idxs:
            return
        for idx in sorted(set(idxs), reverse=True):
            if 0 <= idx < len(self.words_ref):
                del self.words_ref[idx]
        self.refresh()
        if self.on_changed:
            self.on_changed()
