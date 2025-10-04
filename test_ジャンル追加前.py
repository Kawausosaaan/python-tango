import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
import random
import secrets  # ★追加（使ってもOKだけど下は SystemRandom で統一）
import json
from pathlib import Path
from typing import List, Dict, Optional

# ===================== json =====================
class WordRepository:
    """words.json を読み書きするだけの薄い層"""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else Path(__file__).with_name("words.json")

    def load(self) -> List[Dict[str, str]]:
        if not self.path.exists():
            return []
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return [
                {"word": str(d.get("word", "")), "meaning": str(d.get("meaning", ""))}
                for d in data if isinstance(d, dict)
            ]
        except Exception:
            return []

    def save(self, words: List[Dict[str, str]]) -> None:
        try:
            with self.path.open("w", encoding="utf-8") as f:
                json.dump(words, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # おまけ: 単語操作のユーティリティ（使わなくてもOK）
    def add(self, words: List[Dict[str, str]], w: str, m: str) -> None:
        words.append({"word": w, "meaning": m})
        self.save(words)

    def delete_indices(self, words: List[Dict[str, str]], idxs: List[int]) -> None:
        for i in sorted(set(idxs), reverse=True):
            if 0 <= i < len(words):
                del words[i]
        self.save(words)


# ===================== 子ウィンドウ: 単語追加 =====================
class AddWordDialog(tk.Toplevel):
    def __init__(self, parent, on_submit, initial=None, title="単語追加"):
        super().__init__(parent)
        self.title(title)
        self.on_submit = on_submit   # 保存時に item を返す汎用コールバック
        self.initial = initial or {"word": "", "meaning": ""}

        self._build()

        self.transient(parent)
        self.update_idletasks()
        self._center_over_parent(parent, y_offset=-300)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def _build(self):
        pad = {"padx": 10, "pady": 6}
        self.columnconfigure(1, weight=1)

        # --- 単語 ---
        tk.Label(self, text="単語:").grid(row=0, column=0, sticky="nw", **pad)
        word_wrap = tk.Frame(self)
        word_wrap.grid(row=0, column=1, sticky="nsew", **pad)
        word_wrap.columnconfigure(0, weight=1)

        self.e_word = tk.Text(word_wrap, width=40, height=5, font=("Meiryo", 12), wrap="word")
        self.e_word.grid(row=0, column=0, sticky="nsew")
        sbw = tk.Scrollbar(word_wrap, command=self.e_word.yview)
        sbw.grid(row=0, column=1, sticky="ns")
        self.e_word.config(yscrollcommand=sbw.set)
        # 初期値
        self.e_word.insert("1.0", self.initial.get("word", ""))

        # --- 意味 ---
        tk.Label(self, text="意味:").grid(row=1, column=0, sticky="nw", **pad)
        mean_wrap = tk.Frame(self)
        mean_wrap.grid(row=1, column=1, sticky="nsew", **pad)
        mean_wrap.columnconfigure(0, weight=1)

        self.e_mean = tk.Text(mean_wrap, width=40, height=5, font=("Meiryo", 12), wrap="word")
        self.e_mean.grid(row=0, column=0, sticky="nsew")
        sbm = tk.Scrollbar(mean_wrap, command=self.e_mean.yview)
        sbm.grid(row=0, column=1, sticky="ns")
        self.e_mean.config(yscrollcommand=sbm.set)
        # 初期値
        self.e_mean.insert("1.0", self.initial.get("meaning", ""))

        # ボタン
        btns = tk.Frame(self)
        btns.grid(row=2, column=0, columnspan=2, pady=10)

        tk.Button(btns, text="保存", command=self._submit, width=10).pack(side="left", padx=6)
        tk.Button(btns, text="キャンセル", command=self._cancel, width=10).pack(side="left", padx=6)

        # キーバインド
        self.bind("<Control-Return>", lambda e: self._submit())  # Ctrl+Enterで保存
        self.bind("<Escape>",        lambda e: self._cancel())   # Escでキャンセル
        self.e_word.focus_set()

    def _submit(self):
        # Text から取得
        w = self.e_word.get("1.0", "end-1c").strip()
        m = self.e_mean.get("1.0", "end-1c").strip()
        if self.on_submit and (w or m):
            self.on_submit({"word": w, "meaning": m})
        self.destroy()

    def _center_over_parent(self, parent, y_offset=0):
        """親ウィンドウ中央に配置（y_offsetで上下微調整も可）"""
        # 親の実画面座標とサイズ
        parent.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()  or parent.winfo_reqwidth()
        ph = parent.winfo_height() or parent.winfo_reqheight()

        # 自分のサイズ
        self.update_idletasks()
        dw = self.winfo_width()  or self.winfo_reqwidth()
        dh = self.winfo_height() or self.winfo_reqheight()

        # 親の中央座標
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2 + y_offset

        # 画面外に出ないように軽くガード
        x = max(0, x)
        y = max(0, y)

        # 位置だけ指定（サイズはそのまま）
        self.geometry(f"+{x}+{y}")

    def _cancel(self):
        self.destroy()








# ===================== 子ウィンドウ: 単語一覧 =====================
class WordListWindow(tk.Toplevel):
    def __init__(self, parent, words_ref, on_deleted=None):
        super().__init__(parent)
        self.title("単語一覧")
        self.geometry("640x420")
        self.words_ref = words_ref    # 参照（リストそのもの）
        self.on_deleted = on_deleted  # 削除後の通知（必要なら）
        self._build()
        self.refresh()

    def _build(self):
        columns = ("word", "meaning")
        self.tree = ttk.Treeview(
            self, columns=columns, show="headings", height=15, selectmode="extended"
        )
        self.tree.heading("word", text="単語")
        self.tree.heading("meaning", text="意味")
        self.tree.column("word", width=220, anchor="w")
        self.tree.column("meaning", width=380, anchor="w")

        vsb = tk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Delete キーで削除
        self.tree.bind("<Delete>", self._on_delete_key)
        # ★ ダブルクリックで編集
        self.tree.bind("<Double-1>", self._on_double_click)

    def _on_double_click(self, _evt=None):
        iid = self.tree.focus()
        if not iid:
            return
        try:
            idx = int(iid.split("-")[1])
        except Exception:
            return
        if not (0 <= idx < len(self.words_ref)):
            return

        # 現在値を取得して編集ダイアログを開く
        current = dict(self.words_ref[idx])  # {"word":..., "meaning":...}

        def on_submit(updated):
            # 更新して再描画
            self.words_ref[idx] = {
                "word": updated.get("word", ""),
                "meaning": updated.get("meaning", "")
            }
            self.refresh()
            if self.on_deleted:   # 保存先（JSON等）に反映したいならここを流用
                self.on_deleted()

        # 既存の AddWordDialog を“編集モード”で再利用
        AddWordDialog(
            self, on_submit=on_submit,
            initial=current, title="単語を編集"
        )


    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, item in enumerate(self.words_ref):
            self.tree.insert("", "end", iid=f"row-{i}",
                             values=(item.get("word", ""), item.get("meaning", "")))

    def _on_delete_key(self, _evt=None):
        sel = list(self.tree.selection())
        if not sel:
            return
        idxs = []
        for iid in sel:
            try:
                idxs.append(int(iid.split("-")[1]))
            except Exception:
                pass
        if not idxs:
            return
        for idx in sorted(set(idxs), reverse=True):
            if 0 <= idx < len(self.words_ref):
                del self.words_ref[idx]
        self.refresh()
        if self.on_deleted:
            self.on_deleted()


# ===================== 本体アプリ =====================
class WordApp:
    def __init__(self, words):
        self.repo = WordRepository()                 # ← 追加
        self.words = words[:] if words is not None else self.repo.load()
        self.current_word = None
        self.current_index = -1

        self.root = tk.Tk()
        self.root.title("単語帳アプリ")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._place_right_half()
        self._create_widgets()
        self._bind_keys()
        # 並び順と位置（起動ごとにシャッフル、セッション中は固定）
        self.order: list[int] = []
        self.pos: int = -1
        self._build_order()

    # --- レイアウト ---
    def _place_right_half(self):
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        ww, wh = sw // 2, sh
        self.root.geometry(f"{ww}x{wh}+{sw//2}+0")

    def _create_widgets(self):
        top = tk.Frame(self.root)
        top.pack(side="top", pady=10)

        tk.Button(top, text="単語を表示（次へ）", command=self.next_word).pack(side="left", padx=5)
        tk.Button(top, text="意味を表示", command=self.show_meaning).pack(side="left", padx=5)
        tk.Button(top, text="単語を追加", command=self.open_add_window).pack(side="left", padx=5)
        tk.Button(top, text="単語一覧", command=self.open_list_window).pack(side="left", padx=5)

        self.word_area = self._make_text_row(("Meiryo", 14), ("Arial", 14), ("Meiryo", 14),init_height=1, min_h=1, max_h=6)
        # OK（このまま置き換え）
        self.meaning_area = self._make_text_row(("Meiryo", 14), ("Arial", 12), ("Meiryo", 12),init_height=3, min_h=3, max_h=24) # 初期3行、最大12行まで広げる

        self.insert_mixed_text(self.word_area, "")
        self.insert_mixed_text(self.meaning_area, "???")

    # 置き換え
    def _make_text_row(self, base_font, en_tag, ja_tag, width=120,init_height=1, min_h=1, max_h=6):
        row = tk.Frame(self.root)
        row.pack(pady=10, fill="x")

        txt = tk.Text(
            row, wrap="word", height=init_height, width=width, bg="white",
            font=base_font, bd=1, relief="solid", highlightthickness=0
        )
        txt.pack(side="left", fill="x")
        sb = tk.Scrollbar(row, command=txt.yview)
        sb.pack(side="right", fill="y")
        txt.config(yscrollcommand=sb.set)

        txt.tag_config("english", font=en_tag)
        txt.tag_config("japanese", font=ja_tag)
        txt.config(state="disabled")

        # ★ このText専用の自動調整しきい値を持たせる
        txt._auto_min_h = min_h
        txt._auto_max_h = max_h
        return txt

    def _bind_keys(self):
        # a=前へ / d=次へ
        self.root.bind("<a>", lambda e: self.prev_word())
        self.root.bind("<A>", lambda e: self.prev_word())
        self.root.bind("<d>", lambda e: self.next_word())
        self.root.bind("<D>", lambda e: self.next_word())

        self.root.bind("<Return>", self._on_enter_key)
        self.root.bind("<KP_Enter>", self._on_enter_key)
        self.root.focus_set()

    # --- 動作 ---
    def show_word(self):
        self.next_word()

    def show_meaning(self):
        if not self.current_word:
            return
        self.insert_mixed_text(self.meaning_area, self.current_word["meaning"])

    # --- キー ---
    def _on_next_key(self, event):
        if event.widget.winfo_toplevel() is not self.root:
            return
        self.show_word()

    def _on_enter_key(self, event):
        if event.widget.winfo_toplevel() is not self.root:
            return
        self.show_meaning()

    # --- 混在表示 ---
    def insert_mixed_text(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        for ch in text:
            widget.insert("end", ch, "japanese" if self.is_japanese(ch) else "english")
        widget.config(state="disabled")

        # ★ 固定6行ではなく、各Textに持たせた値を使う
        min_h = getattr(widget, "_auto_min_h", 1)
        max_h = getattr(widget, "_auto_max_h", 6)
        self._adjust_text_size(widget, min_height=min_h, max_height=max_h)

    def _build_order(self):
        """現在の words からセッション専用のランダム順を作る（開始位置もランダム）"""
        n = len(self.words)
        self.order = list(range(n))
        sysrand = random.SystemRandom()
        sysrand.shuffle(self.order)        # OS乱数でシャッフル

        if n > 1:
            start = sysrand.randrange(n)   # ランダム出発点
            self.order = self.order[start:] + self.order[:start]

        self.pos = -1  # まだ何も表示していない


    def _rebuild_order_after_change(self, retain_current=True):
        """
        追加/削除後に順番を作り直す。
        retain_current=True のとき、今表示中が残っていれば先頭に据え直す。
        """
        n = len(self.words)
        self.order = list(range(n))
        sysrand = random.SystemRandom()
        sysrand.shuffle(self.order)

        current_idx = self.current_index if (retain_current and 0 <= self.current_index < n) else None
        if current_idx is not None:
            # 現在の単語を先頭へ（＝次/前の関係が極力保たれる）
            if current_idx in self.order:
                self.order.remove(current_idx)
            self.order.insert(0, current_idx)
            self.pos = 0
        else:
            # 出だしも毎回ズラす
            if n > 1:
                start = sysrand.randrange(n)
                self.order = self.order[start:] + self.order[:start]
            self.pos = -1


    def next_word(self):
        if not self.order:
            self.insert_mixed_text(self.word_area, "(単語がありません)")
            self.insert_mixed_text(self.meaning_area, "")
            return
        self.pos = (self.pos + 1) % len(self.order)
        idx = self.order[self.pos]
        self.current_index = idx
        self.current_word = self.words[idx]
        self.insert_mixed_text(self.word_area, self.current_word["word"])
        self.insert_mixed_text(self.meaning_area, "???")

    def prev_word(self):
        if not self.order:
            self.insert_mixed_text(self.word_area, "(単語がありません)")
            self.insert_mixed_text(self.meaning_area, "")
            return
        self.pos = (self.pos - 1) % len(self.order)
        idx = self.order[self.pos]
        self.current_index = idx
        self.current_word = self.words[idx]
        self.insert_mixed_text(self.word_area, self.current_word["word"])
        self.insert_mixed_text(self.meaning_area, "???")



    @staticmethod
    def is_japanese(ch: str) -> bool:
        code = ord(ch)
        return (
            0x3040 <= code <= 0x30FF  # ひらがな・カタカナ
            or 0x4E00 <= code <= 0x9FFF  # 漢字
            or 0xFF66 <= code <= 0xFF9D  # 半角カナ
        )

    def _adjust_text_size(self, widget, min_height=1, max_height=6):
        widget.update_idletasks()
        usable_w = widget.winfo_width() or widget.winfo_reqwidth()
        font_name = widget.tag_cget("english", "font") or widget.cget("font")
        f = tkfont.Font(root=widget, font=font_name)
        text = widget.get("1.0", "end-1c")
        if not text:
            widget.config(height=min_height)
            return
        line_px = 0
        lines = 1
        for ch in text:
            if ch == "\n":
                lines += 1; line_px = 0; continue
            w = f.measure(ch)
            if line_px + w > max(1, usable_w):
                lines += 1; line_px = w
            else:
                line_px += w
        widget.config(height=max(min_height, min(max_height, lines)))

    # --- ランダム選択（現在とかぶらない） ---
    def _pick_next_index(self) -> int:
        n = len(self.words)
        if n == 0: return -1
        if n == 1: return 0
        nxt = random.randrange(n)
        if nxt == self.current_index:
            nxt = (nxt + 1) % n
        return nxt

    # --- 子ウィンドウ呼び出し ---
    def open_add_window(self):
        def on_submit(item):
            self.words.append(item)
            self.repo.save(self.words)
            self._rebuild_order_after_change(retain_current=True)  # ★ ここ追加
        AddWordDialog(self.root, on_submit=on_submit, title="単語追加")



    def on_close(self):
        self.repo.save(self.words)                   # ← 保存して終了
        self.root.destroy()

    def open_list_window(self):
        def after_delete():
            self.repo.save(self.words)
            self._rebuild_order_after_change(retain_current=True)  # ★ ここ追加
            # 表示中が消えていたらクリア（rebuild 内で pos を-1にしてある）
            if not (0 <= self.current_index < len(self.words)):
                self.current_index = -1
                self.current_word = None
                self.insert_mixed_text(self.word_area, "")
                self.insert_mixed_text(self.meaning_area, "???")
        WordListWindow(self.root, self.words, on_deleted=after_delete)

    # --- 実行 ---
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    repo = WordRepository()
    loaded = repo.load()
    seed = [
        {"word": "apple", "meaning": "りんご"},
        {"word": "book", "meaning": "本"},
        {"word": "computer", "meaning": "コンピュータ"},
    ]
    # 既存ファイルがあればそれを、無ければシードを
    WordApp(loaded or seed).run()

