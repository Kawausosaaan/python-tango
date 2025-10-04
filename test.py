from __future__ import annotations

import json
import random
import tkinter as tk
import tkinter.font as tkfont
import tkinter.ttk as ttk
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

# ===================== Types =====================
WordItem = Dict[str, str]  # {"word": str, "meaning": str, "genre"?: str}


# ===================== Repository =====================
class WordRepository:
    """Load/save a simple word list JSON next to this file."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else Path(__file__).with_name("words.json")

    def load(self) -> List[WordItem]:
        if not self.path.exists():
            return []
        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            # Accept either a list or an object with "words"
            if isinstance(raw, dict) and "words" in raw:
                raw = raw["words"]
            if not isinstance(raw, list):
                return []
            out: List[WordItem] = []
            for d in raw:
                if isinstance(d, dict):
                    item: WordItem = {
                        "word": str(d.get("word", "")),
                        "meaning": str(d.get("meaning", "")),
                    }
                    g = d.get("genre")
                    if isinstance(g, str) and g:
                        item["genre"] = g
                    out.append(item)
            return out
        except Exception:
            return []

    def save(self, words: List[WordItem]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(words, f, ensure_ascii=False, indent=2)
            tmp.replace(self.path)
        except Exception:
            pass

    # helpers (optional use)
    def add(self, words: List[WordItem], w: str, m: str, genre: str = "") -> None:
        item: WordItem = {"word": w, "meaning": m}
        if genre:
            item["genre"] = genre
        words.append(item)
        self.save(words)

    def delete_indices(self, words: List[WordItem], idxs: Iterable[int]) -> None:
        for i in sorted(set(idxs), reverse=True):
            if 0 <= i < len(words):
                del words[i]
        self.save(words)

    def update(self, words: List[WordItem], idx: int, item: WordItem) -> None:
        if 0 <= idx < len(words):
            merged: WordItem = {
                "word": str(item.get("word", "")),
                "meaning": str(item.get("meaning", "")),
            }
            g = item.get("genre")
            if isinstance(g, str) and g:
                merged["genre"] = g
            words[idx] = merged
            self.save(words)


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


# ===================== Left Pane: Genre Tree =====================
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
        # ▼追加：Treeviewにフォーカスを取らせず、クリックで親(Toplevel)へ戻す
        self.tree.configure(takefocus=False)
        self.tree.bind(
            "<Button-1>", lambda e: self.winfo_toplevel().focus_set(), add="+"
        )

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

        for iid in self.tree.get_children(""):
            self.tree.item(iid, open=True)

    def _on_select(self, _evt=None) -> None:
        if self.on_select_iid:
            sel = self.tree.selection()
            if sel:
                self.on_select_iid(sel[0])


# ===================== Right Pane: Study =====================
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
        txt._auto_min_h = min_h  # type: ignore[attr-defined]
        txt._auto_max_h = max_h  # type: ignore[attr-defined]
        return txt

    def set_word(self, text: str) -> None:
        self._renderer(self.word_area, text)

    def set_meaning(self, text: str) -> None:
        self._renderer(self.meaning_area, text)


# ===================== Main App (composes left/right) =====================
class WordApp:
    def __init__(self, words: List[WordItem]):
        self.repo = WordRepository()
        self.words = words[:] if words is not None else self.repo.load()
        self.current_word: Optional[WordItem] = None
        self.current_index: int = -1

        self.root = tk.Tk()
        self.root.title("単語帳アプリ")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._place_right_half()

        # order state (session-fixed)
        self.order: List[int] = []
        self.pos: int = -1
        self.active_parent: str = ""
        self.cursor_in_parent: int = -1

        self._create_widgets()
        self._bind_keys()
        self._build_order()  # initial random order

    # ----- layout -----
    def _place_right_half(self) -> None:
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        ww, wh = sw // 2, sh
        self.root.geometry(f"{ww}x{wh}+{sw // 2}+0")

    def _create_widgets(self) -> None:
        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True)

        # left
        self.left = GenreTreePane(main, on_select_iid=self._on_tree_select_iid)
        self.left.pack(side="left", fill="y")
        self.left.pack_propagate(False)
        self.left.configure(width=260)

        # right
        self.right = StudyPane(
            main,
            on_next=self.next_word,
            on_show_meaning=self.show_meaning,
            on_add=self.open_add_window,
            on_list=self.open_list_window,
            renderer=self.insert_mixed_text,
        )
        self.right.pack(side="left", fill="both", expand=True)

        self.left.rebuild(self.words)
        t = self.left.tree
        gs = list(t.get_children(""))
        if gs:
            self.active_parent = gs[0]  # 先頭のジャンル
            ws = [c for c in t.get_children(self.active_parent) if c.startswith("w:")]
            ws.sort(key=t.index)  # ツリーの見た目順
            if ws:
                self.cursor_in_parent = random.SystemRandom().randrange(len(ws))
                self._apply_cursor()

    # ----- key binds -----
    def _bind_keys(self) -> None:
        self._bind_global("<KeyPress-a>", lambda e: self.prev_word())
        self._bind_global("<KeyPress-A>", lambda e: self.prev_word())
        self._bind_global("<KeyPress-Left>", lambda e: self.prev_word())
        self._bind_global("<KeyPress-d>", lambda e: self.next_word())
        self._bind_global("<KeyPress-D>", lambda e: self.next_word())
        self._bind_global("<KeyPress-Right>", lambda e: self.next_word())
        self._bind_global("<Return>", self._on_enter_key)
        self._bind_global("<KP_Enter>", self._on_enter_key)
        self.root.focus_set()

    # WordApp 内に追加（Treeview フォーカス時のキーを横取りして学習操作へ）
    def _on_tree_key(self, e):
        ks = e.keysym
        # a/d はツリー上では逆向きに感じるのでここだけ入れ替え
        if ks in ("a", "A"):
            self.next_word()
            return "break"
        if ks in ("d", "D"):
            self.prev_word()
            return "break"
        if ks == "Left":
            self.prev_word()
            return "break"
        if ks == "Right":
            self.next_word()
            return "break"
        if ks in ("Return", "KP_Enter"):
            self._on_enter_key()
            return "break"

    # WordApp 内に追加
    def _on_enter_key(self, _evt=None) -> None:
        self.show_meaning()

    def _bind_global(self, sequence: str, handler: Callable[[tk.Event], None]) -> None:
        self.root.bind_all(sequence, lambda e: self._if_main_window(handler, e))

    def _if_main_window(
        self, handler: Callable[[tk.Event], None], event: tk.Event
    ) -> None:
        if event.widget.winfo_toplevel() is self.root:
            handler(event)

    # ----- tree selection -> order -----
    def _on_tree_select_iid(self, iid: str) -> None:
        t = self.left.tree

        if iid.startswith("w:"):
            parent = t.parent(iid)
            self.active_parent = parent
            ws = [c for c in t.get_children(parent) if c.startswith("w:")]
            ws.sort(key=t.index)
            self.cursor_in_parent = ws.index(iid) if iid in ws else -1
            self._apply_cursor()
            self.root.after(0, self.root.focus_set)
            return

        elif iid.startswith("g:"):
            self.active_parent = iid
            ws = [c for c in t.get_children(iid) if c.startswith("w:")]
            ws.sort(key=t.index)
            if ws:
                self.cursor_in_parent = random.SystemRandom().randrange(len(ws))
                self._apply_cursor()
            else:
                self.cursor_in_parent = -1
                self.right.set_word("(単語がありません)")
                self.right.set_meaning("")
            self.root.after(0, self.root.focus_set)
            return

        else:
            # フォールバック：全ノードをツリー表示順で
            all_children = []
            for g in t.get_children(""):
                all_children.extend(t.get_children(g))
            self.order = [
                int(c.split(":")[1]) for c in all_children if c.startswith("w:")
            ]
            self.pos = -1

        self.next_word()
        self.root.after(0, self.root.focus_set)

    def _build_order_from_indices(self, idxs: List[int]) -> None:
        # ツリーの見た目順そのままをベースに、開始位置だけランダムに回転
        self.order = idxs[:]
        n = len(self.order)
        if n > 1:
            start = random.SystemRandom().randrange(n)
            self.order = self.order[start:] + self.order[:start]
        self.pos = -1

        def _siblings_words(self) -> List[str]:
            t = self.left.tree
            parent = self.active_parent or ""

            # ▼追加：親が未設定なら、選択や先頭ジャンルから推定
            if not parent:
                sel = t.selection()
                if sel:
                    parent = t.parent(sel[0]) if sel[0].startswith("w:") else sel[0]
                if not parent:
                    gs = list(t.get_children(""))
                    if gs:
                        parent = gs[0]
                self.active_parent = parent

            if not parent:
                return []

            ws = [c for c in t.get_children(parent) if c.startswith("w:")]
            ws.sort(key=t.index)  # ツリーの見た目順
            return ws

    def _siblings_words(self) -> List[str]:
        t = self.left.tree
        parent = self.active_parent or ""

        # 親が未設定なら、選択や先頭ジャンルから推定
        if not parent:
            sel = t.selection()
            if sel:
                parent = t.parent(sel[0]) if sel[0].startswith("w:") else sel[0]
            if not parent:
                gs = list(t.get_children(""))
                if gs:
                    parent = gs[0]
            self.active_parent = parent

        if not parent:
            return []

        ws = [c for c in t.get_children(parent) if c.startswith("w:")]
        ws.sort(key=t.index)  # ツリーの見た目順
        return ws

    def _apply_cursor(self) -> None:
        ws = self._siblings_words()
        if not ws or not (0 <= self.cursor_in_parent < len(ws)):
            return
        iid = ws[self.cursor_in_parent]
        idx = int(iid.split(":")[1])
        self.current_index = idx
        self.current_word = self.words[idx]
        self.right.set_word(self.current_word.get("word", ""))
        self.right.set_meaning("???")
        self.left.tree.selection_set(iid)
        self.left.tree.focus(iid)
        self.left.tree.see(iid)

    # ▼追加：選択中ジャンルの直下にある単語ノードを、idxs の順に並べ替える
    def _reorder_tree_for_selection(self, iid: str, idxs: List[int]) -> None:
        tree = self.left.tree
        parent = iid if iid.startswith("g:") else tree.parent(iid)
        if not parent:
            return

        # 親配下の "w:{index}" → child iid をマップ化
        idx_to_iid = {}
        for child in tree.get_children(parent):
            if child.startswith("w:"):
                try:
                    idx_to_iid[int(child.split(":")[1])] = child
                except Exception:
                    pass

        # idxs の順に move して並び替え
        for pos, idx in enumerate(idxs):
            item = idx_to_iid.get(idx)
            if item:
                tree.move(item, parent, pos)

    # ▼追加：現在の単語をツリー上で選択・スクロール
    def _sync_tree_selection(self) -> None:
        if 0 <= self.current_index < len(self.words):
            iid = f"w:{self.current_index}"
            if self.left.tree.exists(iid):
                self.left.tree.selection_set(iid)
                self.left.tree.see(iid)

    # ----- study actions -----
    def next_word(self) -> None:
        """ツリーの表示順で次の単語へ（兄弟ノード順に従う）"""
        ws = self._siblings_words()
        if not ws:
            self.right.set_word("(単語がありません)")
            self.right.set_meaning("")
            return

        # カーソル未設定なら先頭から、以降は +1 で巡回
        if self.cursor_in_parent < 0 or self.cursor_in_parent >= len(ws):
            self.cursor_in_parent = 0
        else:
            self.cursor_in_parent = (self.cursor_in_parent + 1) % len(ws)

        self._apply_cursor()

    def prev_word(self) -> None:
        """ツリーの表示順で前の単語へ（兄弟ノード順に従う）"""
        ws = self._siblings_words()
        if not ws:
            self.right.set_word("(単語がありません)")
            self.right.set_meaning("")
            return

        # カーソル未設定なら末尾から、以降は -1 で巡回
        if self.cursor_in_parent < 0 or self.cursor_in_parent >= len(ws):
            self.cursor_in_parent = len(ws) - 1
        else:
            self.cursor_in_parent = (self.cursor_in_parent - 1) % len(ws)

        self._apply_cursor()

    def show_meaning(self) -> None:
        if self.current_word:
            self.right.set_meaning(self.current_word.get("meaning", ""))

    # ----- renderer (mixed JP/EN with auto height) -----
    def insert_mixed_text(self, widget: tk.Text, text: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        for ch in text:
            widget.insert("end", ch, "japanese" if self.is_japanese(ch) else "english")
        widget.configure(state="disabled")
        min_h = getattr(widget, "_auto_min_h", 1)
        max_h = getattr(widget, "_auto_max_h", 6)
        self._adjust_text_size(widget, min_height=min_h, max_height=max_h)

    @staticmethod
    def is_japanese(ch: str) -> bool:
        code = ord(ch)
        return (
            (0x3040 <= code <= 0x30FF)
            or (0x4E00 <= code <= 0x9FFF)
            or (0xFF66 <= code <= 0xFF9D)
        )

    def _adjust_text_size(
        self, widget: tk.Text, min_height: int = 1, max_height: int = 6
    ) -> None:
        widget.update_idletasks()
        usable_w = widget.winfo_width() or widget.winfo_reqwidth()
        font_name = widget.tag_cget("english", "font") or widget.cget("font")
        f = tkfont.Font(root=widget, font=font_name)
        text = widget.get("1.0", "end-1c")
        if not text:
            widget.configure(height=min_height)
            return
        line_px = 0
        lines = 1
        for ch in text:
            if ch == "\n":
                lines += 1
                line_px = 0
                continue
            w = f.measure(ch)
            if line_px + w > max(1, usable_w):
                lines += 1
                line_px = w
            else:
                line_px += w
        widget.configure(height=max(min_height, min(max_height, lines)))

    # ----- order lifecycle -----
    def _build_order(self) -> None:
        n = len(self.words)
        self.order = list(range(n))
        sysrand = random.SystemRandom()
        sysrand.shuffle(self.order)
        if n > 1:
            start = sysrand.randrange(n)
            self.order = self.order[start:] + self.order[:start]
        self.pos = -1

    def _rebuild_order_after_change(self, retain_current: bool = True) -> None:
        n = len(self.words)
        self.order = list(range(n))
        sysrand = random.SystemRandom()
        sysrand.shuffle(self.order)
        current_idx = (
            self.current_index
            if (retain_current and 0 <= self.current_index < n)
            else None
        )
        if current_idx is not None:
            if current_idx in self.order:
                self.order.remove(current_idx)
            self.order.insert(0, current_idx)
            self.pos = 0
        else:
            if n > 1:
                start = sysrand.randrange(n)
                self.order = self.order[start:] + self.order[:start]
            self.pos = -1

    # ----- child windows -----
    def open_add_window(self) -> None:
        def on_submit(item: WordItem) -> None:
            self.words.append(item)
            self.repo.save(self.words)
            self.left.rebuild(self.words)
            self._rebuild_order_after_change(retain_current=True)

        AddWordDialog(self.root, on_submit=on_submit, title="単語追加")

    def open_list_window(self) -> None:
        def on_changed() -> None:
            self.repo.save(self.words)
            self.left.rebuild(self.words)
            self._rebuild_order_after_change(retain_current=True)
            if not (0 <= self.current_index < len(self.words)):
                self.current_index = -1
                self.current_word = None
                self.right.set_word("")
                self.right.set_meaning("???")

        WordListWindow(self.root, self.words, on_changed=on_changed)

    # ----- shutdown -----
    def on_close(self) -> None:
        self.repo.save(self.words)
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()

        # ----- tree selection -> order -----

    def _collect_word_indices_under(self, iid: str) -> List[int]:
        """指定iid配下の w: ノードを、Treeviewの表示順どおりに再帰収集。"""
        out: List[int] = []
        for child in self.left.tree.get_children(iid):
            if child.startswith("w:"):
                out.append(int(child.split(":")[1]))
            elif child.startswith("g:"):
                out.extend(self._collect_word_indices_under(child))
        return out


# ===================== Entrypoint =====================
if __name__ == "__main__":
    repo = WordRepository()
    loaded = repo.load()
    initial_words: List[WordItem] = [
        {"word": "apple", "meaning": "りんご", "genre": "食べ物/果物"},
        {"word": "book", "meaning": "本", "genre": "学校/道具"},
        {"word": "computer", "meaning": "コンピュータ", "genre": "IT/機器"},
    ]
    WordApp(loaded or initial_words).run()
