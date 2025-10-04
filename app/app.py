from __future__ import annotations

import random
import tkinter as tk
import tkinter.font as tkfont
from typing import Callable, List, Optional

from .dialogs import AddWordDialog
from .list_window import WordListWindow
from .panes import GenreTreePane, StudyPane
from .repository import WordRepository
from .types_ import WordItem


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
        self._suspend_select = False

    # ----- layout -------------------------------------------------------------
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

    # ----- key binds ----------------------------------------------------------
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

    def _on_enter_key(self, _evt=None) -> None:
        self.show_meaning()

    def _bind_global(self, sequence: str, handler: Callable[[tk.Event], None]) -> None:
        self.root.bind_all(sequence, lambda e: self._if_main_window(handler, e))

    # WordApp 内に追加
    def _build_order(self) -> None:
        """旧ランダム巡回用の名残。現在はツリー順ナビなので空実装でOK。"""
        self.order = []
        self.pos = -1

    def _if_main_window(
        self, handler: Callable[[tk.Event], None], event: tk.Event
    ) -> None:
        if event.widget.winfo_toplevel() is self.root:
            handler(event)

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

    # ----- tree selection -> cursor ------------------------------------------
    def _on_tree_select_iid(self, iid: str) -> None:
        if self._suspend_select:
            return
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

    # 可視順の“兄弟ワード” iid リストを取得
    def _siblings_words(self) -> List[str]:
        """現在のアクティブ親（ジャンル）直下にある w: ノードを、Treeview の表示順で返す。"""
        t = self.left.tree
        parent = self.active_parent or ""

        # 親が未設定なら、現在の選択または先頭ジャンルから推定
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
        ws.sort(key=t.index)  # ツリーに見えている順
        return ws

    # カーソル位置(self.cursor_in_parent)を画面と状態へ反映
    def _apply_cursor(self) -> None:
        ws = self._siblings_words()
        if not ws or not (0 <= self.cursor_in_parent < len(ws)):
            return
        iid = ws[self.cursor_in_parent]
        try:
            idx = int(iid.split(":")[1])
        except Exception:
            return

        self.current_index = idx
        self.current_word = self.words[idx]

        # 右側テキスト
        self.right.set_word(self.current_word.get("word", ""))
        self.right.set_meaning("???")

        # ここをガード
        self._suspend_select = True
        try:
            self.left.tree.selection_set(iid)
            self.left.tree.focus(iid)
            self.left.tree.see(iid)
        finally:
            # 即時解除だと同フレームで再発火することがあるので idle 後に解除
            self.root.after_idle(lambda: setattr(self, "_suspend_select", False))

    # ----- study actions ------------------------------------------------------
    def next_word(self) -> None:
        ws = self._siblings_words()
        if not ws:
            self.right.set_word("(単語がありません)")
            self.right.set_meaning("")
            return
        self.cursor_in_parent = (self.cursor_in_parent + 1) % len(ws)
        self._apply_cursor()

    def prev_word(self) -> None:
        ws = self._siblings_words()
        if not ws:
            self.right.set_word("(単語がありません)")
            self.right.set_meaning("")
            return
        self.cursor_in_parent = (self.cursor_in_parent - 1) % len(ws)
        self._apply_cursor()

    def show_meaning(self) -> None:
        if self.current_word:
            self.right.set_meaning(self.current_word.get("meaning", ""))

    # ----- renderer (mixed JP/EN with auto height) ---------------------------
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

    # ----- add/list windows ---------------------------------------------------
    def open_add_window(self) -> None:
        def on_submit(item: WordItem) -> None:
            self.words.append(item)
            self.repo.save(self.words)
            # ツリーを再構築して、現在のジャンルに戻す
            self.left.rebuild(self.words)
            if self.active_parent:
                # 現在のジャンルでカーソルはそのまま（もし該当が消えたら先頭に）
                ws = self._siblings_words()
                if ws:
                    self.cursor_in_parent = min(self.cursor_in_parent, len(ws) - 1)
                    self.cursor_in_parent = max(self.cursor_in_parent, 0)
                    self._apply_cursor()

        AddWordDialog(self.root, on_submit=on_submit, title="単語追加")

    def open_list_window(self) -> None:
        def on_changed() -> None:
            self.repo.save(self.words)
            self.left.rebuild(self.words)
            # 現在ジャンルのカーソルを補正
            if self.active_parent:
                ws = self._siblings_words()
                if ws:
                    # 可能なら同じ単語 idx を探す。なければ範囲内に丸める
                    if 0 <= self.current_index < len(self.words):
                        cur_iid = f"w:{self.current_index}"
                        if cur_iid in ws:
                            self.cursor_in_parent = ws.index(cur_iid)
                        else:
                            self.cursor_in_parent = min(
                                self.cursor_in_parent, len(ws) - 1
                            )
                    else:
                        self.cursor_in_parent = 0
                    self._apply_cursor()
                else:
                    self.cursor_in_parent = -1
                    self.right.set_word("(単語がありません)")
                    self.right.set_meaning("")

        WordListWindow(self.root, self.words, on_changed=on_changed)

    # ----- shutdown -----------------------------------------------------------
    def on_close(self) -> None:
        self.repo.save(self.words)
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()

    # （必要なら）任意ノード配下の w: を可視順で収集
    def _collect_word_indices_under(self, iid: str) -> List[int]:
        out: List[int] = []
        t = self.left.tree
        for child in t.get_children(iid):
            if child.startswith("w:"):
                try:
                    out.append(int(child.split(":")[1]))
                except Exception:
                    pass
            elif child.startswith("g:"):
                out.extend(self._collect_word_indices_under(child))
        return out
