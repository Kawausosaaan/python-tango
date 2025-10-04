# app/panes.py
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


class StudyPane(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        *,
        on_next: Callable[[], None],
        on_show_meaning: Callable[[], None],
        on_add: Callable[[], None],
        on_list: Callable[[], None],
        renderer: Callable[[tk.Text, str], None],
    ) -> None:
        super().__init__(parent)
        self._renderer = renderer
        self._build(on_next, on_show_meaning, on_add, on_list)

    def _build(self, on_next, on_show_meaning, on_add, on_list) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        top = tk.Frame(self)
        top.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 8))
        tk.Button(top, text="単語を表示（次へ）", command=on_next).pack(
            side="left", padx=5
        )
        tk.Button(top, text="意味を表示", command=on_show_meaning).pack(
            side="left", padx=5
        )
        tk.Button(top, text="単語を追加", command=on_add).pack(side="left", padx=5)
        tk.Button(top, text="単語一覧", command=on_list).pack(side="left", padx=5)

        self.word_area = self._make_text_row_in(
            row=1,
            base_font=("Meiryo", 14),
            en_tag=("Arial", 14),
            ja_tag=("Meiryo", 14),
            init_height=1,
            min_h=1,
            max_h=6,
        )
        self.meaning_area = self._make_text_row_in(
            row=2,
            base_font=("Meiryo", 14),
            en_tag=("Arial", 12),
            ja_tag=("Meiryo", 12),
            init_height=3,
            min_h=3,
            max_h=24,
        )

        self.set_word("")
        self.set_meaning("???")

    def _make_text_row_in(
        self,
        *,
        row: int,
        base_font: tuple,
        en_tag: tuple,
        ja_tag: tuple,
        width: int = 120,
        init_height: int = 1,
        min_h: int = 1,
        max_h: int = 6,
    ) -> tk.Text:
        rowf = tk.Frame(self)
        rowf.grid(row=row, column=0, sticky="nwe", padx=16, pady=8)
        rowf.columnconfigure(0, weight=1)
        txt = tk.Text(
            rowf,
            wrap="word",
            height=init_height,
            width=width,
            bg="white",
            font=base_font,
            bd=1,
            relief="solid",
            highlightthickness=0,
        )
        txt.grid(row=0, column=0, sticky="nwe")
        sb = tk.Scrollbar(rowf, orient="vertical", command=txt.yview)
        sb.grid(row=0, column=1, sticky="ns")
        txt.configure(yscrollcommand=sb.set)
        txt.tag_config("english", font=en_tag)
        txt.tag_config("japanese", font=ja_tag)
        txt.configure(state="disabled")
        # 可変高さに使う最小/最大を属性に付与
        txt._auto_min_h = min_h  # type: ignore[attr-defined]
        txt._auto_max_h = max_h  # type: ignore[attr-defined]
        return txt

    def set_word(self, text: str) -> None:
        self._renderer(self.word_area, text)

    def set_meaning(self, text: str) -> None:
        self._renderer(self.meaning_area, text)
