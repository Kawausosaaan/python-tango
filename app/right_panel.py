# app/right_panel.py
from __future__ import annotations

import tkinter as tk
import tkinter.ttk as ttk
from typing import Callable, List

from types_ import WordItem


class RightPanel(tk.Frame):
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
        txt.tag_configure("red", foreground="red")
        txt.tag_configure("blue", foreground="blue")
        return txt

    def set_word(self, text: str) -> None:
        self._renderer(self.word_area, text)

    def set_meaning(self, text: str) -> None:
        self._renderer(self.meaning_area, text)
