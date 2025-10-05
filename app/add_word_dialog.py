# app/add_word_dialog.py
from __future__ import annotations

import tkinter as tk
import tkinter.ttk as ttk
from typing import Callable, Optional

from .types_ import WordItem


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

        # ---- color toolbar ----
        toolbar = tk.Frame(self)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 0))
        tk.Label(toolbar, text="色:").pack(side="left")
        tk.Button(
            toolbar, text="赤", width=4, command=lambda: self._apply_color("red")
        ).pack(side="left", padx=4)
        tk.Button(
            toolbar, text="青", width=4, command=lambda: self._apply_color("blue")
        ).pack(side="left", padx=4)
        tk.Button(
            toolbar, text="黒", width=4, command=lambda: self._apply_color("black")
        ).pack(side="left", padx=4)
        tk.Label(toolbar, text="（選択した範囲に適用）").pack(side="left", padx=8)

        # word
        tk.Label(self, text="単語:").grid(row=1, column=0, sticky="nw", **pad)
        wwrap = tk.Frame(self)
        wwrap.grid(row=1, column=1, sticky="nsew", **pad)
        wwrap.columnconfigure(0, weight=1)
        self.e_word = tk.Text(
            wwrap, width=40, height=5, font=("Meiryo", 12), wrap="word", undo=True
        )
        self.e_word.grid(row=0, column=0, sticky="nsew")
        sbw = tk.Scrollbar(wwrap, command=self.e_word.yview)
        sbw.grid(row=0, column=1, sticky="ns")
        self.e_word.configure(yscrollcommand=sbw.set)
        self.e_word.insert("1.0", self.initial.get("word", ""))

        # meaning
        tk.Label(self, text="意味:").grid(row=2, column=0, sticky="nw", **pad)
        mwrap = tk.Frame(self)
        mwrap.grid(row=2, column=1, sticky="nsew", **pad)
        mwrap.columnconfigure(0, weight=1)
        self.e_mean = tk.Text(
            mwrap, width=40, height=5, font=("Meiryo", 12), wrap="word", undo=True
        )
        self.e_mean.grid(row=0, column=0, sticky="nsew")
        sbm = tk.Scrollbar(mwrap, command=self.e_mean.yview)
        sbm.grid(row=0, column=1, sticky="ns")
        self.e_mean.configure(yscrollcommand=sbm.set)
        self.e_mean.insert("1.0", self.initial.get("meaning", ""))

        # genre
        tk.Label(self, text="ジャンル（例: 食べ物/果物）:").grid(
            row=3, column=0, sticky="w", padx=10, pady=6
        )
        self.e_genre = tk.Entry(self, width=40, font=("Meiryo", 12))
        self.e_genre.grid(row=3, column=1, sticky="ew", ipady=4, padx=10, pady=6)
        self.e_genre.insert(0, self.initial.get("genre", ""))

        # buttons
        btns = tk.Frame(self)
        btns.grid(row=4, column=0, columnspan=2, pady=10)
        tk.Button(btns, text="保存", width=10, command=self._submit).pack(
            side="left", padx=6
        )
        tk.Button(btns, text="キャンセル", width=10, command=self._cancel).pack(
            side="left", padx=6
        )

        # color tags (両テキストに同じタグ定義)
        for txt in (self.e_word, self.e_mean):
            txt.tag_configure("fg::red", foreground="red")
            txt.tag_configure("fg::blue", foreground="blue")
            # black は「色を外す」動作にするのでタグは不要でもよいが、
            # 明示したい場合は下記を有効化：
            # txt.tag_configure("black", foreground="black")

        # keys
        # ショートカット: Ctrl-1=赤, Ctrl-2=青, Ctrl-3=黒
        self.bind("<Control-Key-1>", lambda e: self._apply_color("red"))
        self.bind("<Control-Key-2>", lambda e: self._apply_color("blue"))
        self.bind("<Control-Key-3>", lambda e: self._apply_color("black"))

        self.e_word.focus_set()

    # --- ここは _submit（※ クラス直下のインデントに置いてね！）---
    def _submit(self) -> None:
        def collect_runs(txt: tk.Text) -> list:
            content = txt.get("1.0", "end-1c")
            if not content:
                return []
            runs = []
            i = 0
            cur_fg = None
            buf = []

            def flush():
                nonlocal buf, cur_fg, runs
                if buf:
                    seg = {"text": "".join(buf)}
                    if cur_fg:
                        seg["fg"] = cur_fg
                    runs.append(seg)
                    buf = []

            for ch in content:
                index = f"1.0 + {i} chars"
                tags = txt.tag_names(index)
                # fg:: の最初を採用
                fg = None
                for t in tags:
                    if t.startswith("fg::"):
                        fg = t[4:]  # "fg::red" -> "red"
                        break
                if fg != cur_fg:
                    flush()
                    cur_fg = fg
                buf.append(ch)
                i += 1

            flush()
            return runs

        w = self.e_word.get("1.0", "end-1c").strip()
        m = self.e_mean.get("1.0", "end-1c").strip()
        g = self.e_genre.get().strip()

        w_runs = collect_runs(self.e_word)
        m_runs = collect_runs(self.e_mean)

        item = {"word": w, "meaning": m, "genre": g}
        if w_runs:
            item["word_runs"] = w_runs
        if m_runs:
            item["meaning_runs"] = m_runs

        if self.on_submit and (w or m or g or w_runs or m_runs):
            self.on_submit(item)
        self.destroy()

    def _active_text(self) -> tk.Text | None:
        """直近でフォーカスのある Text を返す。なければ None。"""
        w = self.focus_get()
        if isinstance(w, tk.Text):
            return w
        # word/meaning どちらかにフォーカスがない場合は word に適用
        return self.e_word if self.e_word.winfo_exists() else None

    # --- ここは _apply_color（既存）。中身のタグ名だけ直す ---
    def _apply_color(self, color: str) -> None:
        """選択中の範囲に色タグを適用。黒は赤/青タグの削除で実現。"""
        txt = self._active_text()
        if not txt:
            return
        try:
            start = txt.index("sel.first")
            end = txt.index("sel.last")
        except tk.TclError:
            return

        # 既存の色タグ（統一した命名）を外す
        txt.tag_remove("fg::red", start, end)
        txt.tag_remove("fg::blue", start, end)
        if color == "red":
            txt.tag_add("fg::red", start, end)
        elif color == "blue":
            txt.tag_add("fg::blue", start, end)
        else:
            # black: タグ無し=既定色（黒）
            pass

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
