# app/genre_tree_pane.py
from __future__ import annotations

import tkinter as tk
import tkinter.ttk as ttk
from typing import Callable, List

from .types_ import WordItem


class GenreTreePane(tk.Frame):
    """Left pane (tree). Calls back with selected iid string."""

    def __init__(
        self, parent: tk.Widget, *, on_select_iid: Callable[[str], None]
    ) -> None:
        super().__init__(parent)
        self.on_select_iid = on_select_iid
        self._build()

    def _build(self) -> None:
        self.tree = ttk.Treeview(self, show="tree", selectmode="browse")
        ys = tk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ys.set)
        self.tree.pack(side="left", fill="both", expand=True)
        ys.pack(side="right", fill="y")
        # Treeview にフォーカスを残さない（a/d をグローバルで取りやすくする）
        self.tree.configure(takefocus=False)
        self.tree.bind(
            "<Button-1>", lambda e: self.winfo_toplevel().focus_set(), add="+"
        )

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def rebuild(self, words: List[WordItem]) -> None:
        self.tree.delete(*self.tree.get_children())
        root_misc = "g:"
        self.tree.insert("", "end", iid=root_misc, text="(未分類)")
        node_map = {"": root_misc}

        def ensure_node(path: str) -> str:
            if path in node_map:
                return node_map[path]
            parts = [p for p in path.split("/") if p]
            parent = ""
            cur = ""
            for i, p in enumerate(parts):
                cur = "/".join(parts[: i + 1])
                if cur in node_map:
                    parent = node_map[cur]
                    continue
                parent = node_map.get("/".join(parts[:i]), "") or ""
                iid = f"g:{cur}"
                self.tree.insert(parent, "end", iid=iid, text=p)
                node_map[cur] = iid
            return node_map[path]

        for i, w in enumerate(words):
            gpath = (w.get("genre") or "").strip()
            parent = ensure_node(gpath) if gpath else root_misc
            self.tree.insert(parent, "end", iid=f"w:{i}", text=w.get("word", ""))

        # ルート直下のジャンルは展開しておく
        for iid in self.tree.get_children(""):
            self.tree.item(iid, open=True)

    def _on_select(self, _evt=None) -> None:
        if self.on_select_iid:
            sel = self.tree.selection()
            if sel:
                self.on_select_iid(sel[0])
