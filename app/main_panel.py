# app/main_panel.py
from __future__ import annotations

import random
import tkinter as tk
import tkinter.font as tkfont
from contextlib import contextmanager
from typing import Callable, List, Optional

from .add_word_dialog import AddWordDialog
from .left_panel import LeftPanel
from .right_panel import RightPanel
from .types_ import WordItem
from .word_list_window import WordListWindow
from .word_repository import WordRepository


class MainPanel:
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

    @contextmanager
    def _suspend_tree_select(self):
        """Treeviewの選択イベントを一時停止（idleで解除）"""
        self._suspend_select = True
        try:
            yield
        finally:
            # 同フレーム再発火を防ぐため idle で解除
            self.root.after_idle(lambda: setattr(self, "_suspend_select", False))

    # ----- layout -------------------------------------------------------------
    def _place_right_half(self) -> None:
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        ww, wh = sw // 2, sh
        self.root.geometry(f"{ww}x{wh}+{sw // 2}+0")

    def _create_widgets(self) -> None:
        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True)

        # left
        self.left = LeftPanel(
            main,
            on_select_iid=self._on_tree_select_iid,
            on_edit_word=self._on_tree_edit_word,
        )

        self.left.pack(side="left", fill="y")
        self.left.pack_propagate(False)
        self.left.configure(width=260)

        # right
        self.right = RightPanel(
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

        def _set_current_from_iid(iid_str: str) -> None:
            # "w:123" -> 123 を current_index に
            try:
                self.current_index = int(iid_str.split(":")[1])
            except Exception:
                self.current_index = -1

        if iid.startswith("w:"):
            parent = t.parent(iid)
            self.active_parent = parent
            ws = [c for c in t.get_children(parent) if c.startswith("w:")]
            ws.sort(key=t.index)
            self.cursor_in_parent = ws.index(iid) if iid in ws else -1

            self._apply_cursor()  # ← 既存のカーソル適用（選択移動など）
            _set_current_from_iid(iid)  # ★ 追加：current_index を更新
            self._update_right_pane()  # ★ 追加：runs 優先で右ペイン描画

            self.root.after(0, self.root.focus_set)
            return

        elif iid.startswith("g:"):
            self.active_parent = iid
            ws = [c for c in t.get_children(iid) if c.startswith("w:")]
            ws.sort(key=t.index)
            if ws:
                # どれかをアクティブに（既存どおり）
                self.cursor_in_parent = random.SystemRandom().randrange(len(ws))
                self._apply_cursor()

                # ★ 追加：いまアクティブな w: を特定して current_index を反映
                # _apply_cursor 内で Tree の選択を変えているなら、その結果から拾う
                try:
                    sel = t.selection()
                    if sel and sel[0].startswith("w:"):
                        _set_current_from_iid(sel[0])
                    else:
                        _set_current_from_iid(ws[self.cursor_in_parent])
                except Exception:
                    _set_current_from_iid(ws[self.cursor_in_parent])

                self.root.after_idle(self._update_right_pane)
            else:
                self.cursor_in_parent = -1
                # 単語が無いときはプレーン表示（ここは runs 無しでOK）
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

        # 既存の “次の単語へ” ロジック
        self.next_word()

        # ★ 追加：next_word() の中で current_index を更新している前提。
        # もししていないなら、そこで更新するか、ここで選択から拾う。
        self._update_right_pane()  # ← 最後に右ペイン更新を一発

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
            cur = self.left.tree.selection()
            if not (cur and cur[0] == iid):
                self.left.tree.selection_set(iid)
            self.left.tree.focus(iid)
            self.left.tree.see(iid)
        finally:
            self.root.after_idle(lambda: setattr(self, "_suspend_select", False))

    # ----- study actions ------------------------------------------------------
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

        # ここから現在語を反映
        iid = ws[self.cursor_in_parent]
        idx = int(iid.split(":")[1])
        self.current_index = idx
        self.current_word = self.words[idx]

        # 単語表示（runs があれば優先）
        w_runs = self.current_word.get("word_runs")
        if isinstance(w_runs, list) and w_runs:
            self._render_runs(self.right.word_area, w_runs)
        else:
            self.right.set_word(self.current_word.get("word", ""))

        # 意味は隠す
        self.right.set_meaning("???")

        # ツリー選択同期（ガード＋重複回避）
        with self._suspend_tree_select():
            cur = self.left.tree.selection()
            if not (cur and cur[0] == iid):
                self.left.tree.selection_set(iid)
            self.left.tree.focus(iid)
            self.left.tree.see(iid)

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

        # ここから現在語を反映
        iid = ws[self.cursor_in_parent]
        idx = int(iid.split(":")[1])
        self.current_index = idx
        self.current_word = self.words[idx]

        # 単語表示（runs があれば優先）
        w_runs = self.current_word.get("word_runs")
        if isinstance(w_runs, list) and w_runs:
            self._render_runs(self.right.word_area, w_runs)
        else:
            self.right.set_word(self.current_word.get("word", ""))

        # 意味は隠す
        self.right.set_meaning("???")

        # ツリー選択同期（ガード＋重複回避）
        with self._suspend_tree_select():
            cur = self.left.tree.selection()
            if not (cur and cur[0] == iid):
                self.left.tree.selection_set(iid)
            self.left.tree.focus(iid)
            self.left.tree.see(iid)

    def show_meaning(self) -> None:
        """現在語の意味を表示（runs があれば優先）"""
        if not self.current_word:
            return
        m_runs = self.current_word.get("meaning_runs")
        if isinstance(m_runs, list) and m_runs:
            self._render_runs(self.right.meaning_area, m_runs)
        else:
            self.right.set_meaning(self.current_word.get("meaning", ""))

    # ----- renderer (mixed JP/EN with auto height) ---------------------------
    def insert_mixed_text(self, widget: tk.Text, text_or_runs) -> None:
        # text_or_runs: str | List[{"text": str, "color": "red"|"blue"|""}]
        widget.configure(state="normal")
        widget.delete("1.0", "end")

        # 色タグが無いと困るので一応定義（重複定義は無害）
        try:
            widget.tag_configure("red", foreground="red")
            widget.tag_configure("blue", foreground="blue")
        except Exception:
            pass

        def put_text(seg_text: str, color_tag: str | None):
            # 1文字ずつ言語タグを付けながら挿入し、色タグは範囲タグで被せる
            start_idx = widget.index("end-1c")
            for ch in seg_text:
                tag = "japanese" if self.is_japanese(ch) else "english"
                widget.insert("end", ch, tag)
            end_idx = widget.index("end-1c")
            if color_tag in ("red", "blue"):
                widget.tag_add(color_tag, start_idx, end_idx)

        if isinstance(text_or_runs, list):
            for run in text_or_runs:
                seg = run.get("text", "")
                color = run.get("color", "")
                put_text(seg, color if color in ("red", "blue") else None)
        else:
            put_text(str(text_or_runs or ""), None)

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

    def _on_tree_edit_word(self, idx: int) -> None:
        if not (0 <= idx < len(self.words)):
            return
        current = dict(self.words[idx])

        def on_submit(updated: WordItem) -> None:
            # 既存をベースに更新（無いキーは残す）
            new_item = {
                "word": updated.get("word", current.get("word", "")),
                "meaning": updated.get("meaning", current.get("meaning", "")),
                "genre": updated.get("genre", current.get("genre", "")),
            }
            # ★ここが肝：runs を反映（無ければ既存を温存）
            if isinstance(updated.get("word_runs"), list):
                new_item["word_runs"] = updated["word_runs"]
            elif "word_runs" in current:
                new_item["word_runs"] = current["word_runs"]

            if isinstance(updated.get("meaning_runs"), list):
                new_item["meaning_runs"] = updated["meaning_runs"]
            elif "meaning_runs" in current:
                new_item["meaning_runs"] = current["meaning_runs"]

            # 反映＆保存
            self.words[idx] = new_item
            self.repo.save(self.words)

            # ツリー再構築＆同じ項目へ戻す
            with self._suspend_tree_select():
                self.left.rebuild(self.words)
                self.current_index = idx
                iid = f"w:{idx}"
                if self.left.tree.exists(iid):
                    cur = self.left.tree.selection()
                    if not (cur and cur[0] == iid):
                        self.left.tree.selection_set(iid)
                    self.left.tree.focus(iid)
                    self.left.tree.see(iid)

            # 右ペインも runs 優先で更新
            self.current_word = self.words[idx]
            w_runs = self.current_word.get("word_runs")
            m_runs = self.current_word.get("meaning_runs")
            if isinstance(w_runs, list) and w_runs:
                self._render_runs(self.right.word_area, w_runs)
            else:
                self.right.set_word(self.current_word.get("word", ""))

            if isinstance(m_runs, list) and m_runs:
                self._render_runs(self.right.meaning_area, m_runs)
            else:
                self.right.set_meaning(self.current_word.get("meaning", ""))

            self._update_right_pane()

        AddWordDialog(
            self.root, on_submit=on_submit, initial=current, title="単語を編集"
        )

    def open_list_window(self) -> None:
        def on_changed() -> None:
            self.repo.save(self.words)
            with self._suspend_tree_select():
                self.left.rebuild(self.words)
                # 現在ジャンルのカーソルを補正
                if self.active_parent:
                    ws = self._siblings_words()
                    if ws:
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
                    else:
                        self.cursor_in_parent = -1
            # Tree側の更新が済んだあとでカーソル反映
            if self.cursor_in_parent >= 0:
                self._apply_cursor()

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

    def _render_with_runs(self, widget: tk.Text, runs, fallback_text: str) -> None:
        """runs(list[{'text','fg','bg','bold','italic','underline'}])があれば優先表示。
        無ければ fallback_text を従来レンダラーで表示。
        """
        if not runs:
            # 既存の混在レンダラーを使用（英日フォント＆高さ自動）
            self.insert_mixed_text(widget, fallback_text)
            return

        # runs で描画
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        for seg in runs:
            text = seg.get("text", "")
            tags = []
            fg = seg.get("fg")
            bg = seg.get("bg")
            if fg:
                t = f"fg_{fg}"
                if not widget.tag_names().__contains__(t):
                    widget.tag_config(t, foreground=fg)
                tags.append(t)
            if bg:
                t = f"bg_{bg}"
                if not widget.tag_names().__contains__(t):
                    widget.tag_config(t, background=bg)
                tags.append(t)
            if seg.get("bold"):
                if "bold" not in widget.tag_names():
                    import tkinter.font as tkfont

                    base = tkfont.Font(font=widget.cget("font"))
                    boldf = tkfont.Font(font=widget.cget("font"))
                    boldf.configure(weight="bold")
                    widget.tag_config("bold", font=boldf)
                tags.append("bold")
            if seg.get("italic"):
                if "italic" not in widget.tag_names():
                    import tkinter.font as tkfont

                    ital = tkfont.Font(font=widget.cget("font"))
                    ital.configure(slant="italic")
                    widget.tag_config("italic", font=ital)
                tags.append("italic")
            if seg.get("underline"):
                if "ul" not in widget.tag_names():
                    widget.tag_config("ul", underline=1)
                tags.append("ul")

            widget.insert("end", text, tuple(tags) if tags else ())
        widget.configure(state="disabled")

        # 高さ自動（既存ヘルパを活用）
        min_h = getattr(widget, "_auto_min_h", 1)
        max_h = getattr(widget, "_auto_max_h", 6)
        self._adjust_text_size(widget, min_height=min_h, max_height=max_h)

    def _render_current(self) -> None:
        """現在の self.current_word を runs 優先で表示（意味は???に）"""
        item = self.current_word or {}
        self._render_with_runs(
            self.right.word_area, item.get("word_runs"), item.get("word", "")
        )
        # 意味は「隠す」仕様のまま
        self.insert_mixed_text(self.right.meaning_area, "???")

    def _render_runs(self, widget: tk.Text, runs: list) -> None:
        """runs = [{"text": "...", "fg": "red/blue/#rrggbb/black", ...}] を描画"""
        widget.configure(state="normal")
        widget.delete("1.0", "end")

        # よく使う前景色タグを用意（なければ作る）
        def ensure_fg_tag(color: str) -> str:
            tag = f"fg::{color}"
            try:
                widget.tag_cget(tag, "foreground")
            except Exception:
                widget.tag_config(tag, foreground=color)
            return tag

        for seg in runs:
            if not isinstance(seg, dict):
                continue
            text = seg.get("text", "")
            if not isinstance(text, str) or text == "":
                continue

            tags = []
            fg = seg.get("fg")
            if isinstance(fg, str) and fg:
                tags.append(ensure_fg_tag(fg))

            # 必要なら太字/斜体/下線なども対応可能（任意）
            # if seg.get("bold") is True: ...
            # if seg.get("underline") is True: ...

            widget.insert("end", text, tuple(tags) if tags else ())
        widget.configure(state="disabled")

    def _update_right_pane(self):
        """現在の self.current_index をもとに右ペインを再描画（runs優先）"""
        # 選択チェック
        if not (0 <= getattr(self, "current_index", -1) < len(self.words)):
            # 何も選択されてないときはクリア
            if hasattr(self.right, "set_word"):
                self.right.set_word("")
            if hasattr(self.right, "set_meaning"):
                self.right.set_meaning("")
            return

        item = self.words[self.current_index]
        w_runs = item.get("word_runs")
        m_runs = item.get("meaning_runs")

        # ---- いったん右ペインをクリア ----
        # 1) clear_* がある場合
        cleared = False
        if hasattr(self.right, "clear_word"):
            self.right.clear_word()
            cleared = True
        if hasattr(self.right, "clear_meaning"):
            self.right.clear_meaning()
            cleared = True

        # 2) なければ Text ウィジェットを直で消す（プロジェクトに合わせて調整）
        if not cleared:
            # 右側の Text が word_area / meaning_area という前提（違うなら名称を合わせて）
            if hasattr(self.right, "word_area"):
                try:
                    self.right.word_area.delete("1.0", "end")
                except Exception:
                    pass
            if hasattr(self.right, "meaning_area"):
                try:
                    self.right.meaning_area.delete("1.0", "end")
                except Exception:
                    pass

        # ---- runs があれば色付きで描画、なければ文字列で表示 ----
        # word
        if isinstance(w_runs, list) and w_runs:
            # _render_runs(self, text_widget, runs_list) という前提
            self._render_runs(self.right.word_area, w_runs)
        else:
            if hasattr(self.right, "set_word"):
                self.right.set_word(item.get("word", ""))

        # meaning は初期表示では隠す（"???"）。表示は show_meaning() に任せる。
        if hasattr(self.right, "set_meaning"):
            self.right.set_meaning("???")
