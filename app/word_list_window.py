# app/word_list_window.py
from __future__ import annotations

import tkinter as tk
import tkinter.ttk as ttk
from typing import Callable, List, Optional

from .add_word_dialog import AddWordDialog
from .types_ import WordItem


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
            # 既存をベースに更新（無いキーは残す）
            new_item = {
                "word": updated.get("word", current.get("word", "")),
                "meaning": updated.get("meaning", current.get("meaning", "")),
                "genre": updated.get("genre", current.get("genre", "")),
            }
            # runs を反映（無ければ既存を温存）
            if isinstance(updated.get("word_runs"), list):
                new_item["word_runs"] = updated["word_runs"]
            elif "word_runs" in current:
                new_item["word_runs"] = current["word_runs"]

            if isinstance(updated.get("meaning_runs"), list):
                new_item["meaning_runs"] = updated["meaning_runs"]
            elif "meaning_runs" in current:
                new_item["meaning_runs"] = current["meaning_runs"]

            self.words_ref[idx] = new_item
            self.refresh()
            if self.on_changed:
                self.on_changed()  # MainPanel 側で repo.save(...) が走る

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
