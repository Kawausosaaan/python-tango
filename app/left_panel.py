from __future__ import annotations

import tkinter as tk
from typing import Callable, Optional, Dict, Any, List, Tuple

WordItem = Dict[str, Any]


class _TreeAdapter:
    def __init__(self, owner: 'LeftPanel') -> None:
        self._o = owner

    def get_children(self, iid: str = "") -> List[str]:
        if iid in ("", None):
            return list(self._o._genre_order)
        if isinstance(iid, str) and iid.startswith("g:"):
            g = iid[2:]
            return list(self._o._genre_to_words.get(g, []))
        return []

    def parent(self, iid: str) -> str:
        if isinstance(iid, str) and iid.startswith("w:"):
            return self._o._word_to_genre.get(iid, "")
        if isinstance(iid, str) and iid.startswith("g:"):
            return ""
        return ""

    def index(self, iid: str) -> int:
        return int(self._o._iid_to_order.get(iid, 1_000_000))

    def selection(self) -> tuple:
        line = self._o._sel_line
        if line is None:
            return ()
        iid = self._o._line_to_iid.get(line)
        return (iid,) if iid else ()

    def selection_set(self, iid: str) -> None:
        self._o._select_by_iid(iid, notify=False)

    def see(self, iid: str) -> None:
        line = self._o._iid_to_line.get(iid)
        if line is not None:
            self._o.text.see(f"{line}.0")

    def identify_row(self, y: int) -> str:
        try:
            index = self._o.text.index(f"@0,{y}")
            ln = int(index.split(".")[0])
            return self._o._line_to_iid.get(ln, "")
        except Exception:
            return ""

    def focus(self, iid: str) -> None:
        self._o._select_by_iid(iid, notify=False)

    def exists(self, iid: str) -> bool:
        if isinstance(iid, str) and iid.startswith("g:"):
            return iid in self._o._genre_order
        return iid in self._o._iid_to_line

    # passthroughs
    def bind(self, *a, **kw):
        return self._o.text.bind(*a, **kw)

    def configure(self, *a, **kw):
        return self._o.text.configure(*a, **kw)

    def yview(self, *a, **kw):
        return self._o.text.yview(*a, **kw)

    def __getattr__(self, name):
        return getattr(self._o.text, name)

    def tag_configure(self, *a, **kw):
        return None


class LeftPanel(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        on_select: Optional[Callable[[str], None]] = None,
        on_select_iid: Optional[Callable[[str], None]] = None,
        on_edit_word: Optional[Callable[[int], None]] = None,
        **_: Any,
    ) -> None:
        super().__init__(parent)
        self.on_select = on_select
        self.on_select_iid = on_select_iid
        self.on_edit_word = on_edit_word

        self.text = tk.Text(self, wrap="none", height=20, undo=False, cursor="arrow")
        self.text.pack(fill="both", expand=True, side="left")
        self.text.configure(state="disabled")

        sb = tk.Scrollbar(self, orient="vertical", command=self.text.yview)
        sb.pack(fill="y", side="right")
        self.text.configure(yscrollcommand=sb.set)

        # color tags
        self.text.tag_configure("fg::red", foreground="red")
        self.text.tag_configure("fg::blue", foreground="blue")
        self.text.tag_configure("fg::default", foreground="black")
        self.text.tag_configure("row::sel", background="#cde8ff")
        self.text.tag_configure("row::genre", foreground="#666", font=("Meiryo", 10, "bold"))

        # events
        self.text.bind("<Button-1>", self._on_click)
        self.text.bind("<Double-1>", self._on_edit)
        self.text.bind("<Return>", self._on_edit)
        self.text.bind("<Up>", self._on_move)
        self.text.bind("<Down>", self._on_move)

        self.tree = _TreeAdapter(self)

        # indices
        self._line_to_iid: Dict[int, str] = {}
        self._iid_to_line: Dict[str, int] = {}
        self._iid_to_order: Dict[str, int] = {}
        self._genre_order: List[str] = []
        self._genre_to_words: Dict[str, List[str]] = {}
        self._word_to_genre: Dict[str, str] = {}
        self._items: List[WordItem] = []
        self._sel_line: Optional[int] = None

    def rebuild(self, items: List[WordItem]) -> None:
        self._items = items
        self._line_to_iid.clear()
        self._iid_to_line.clear()
        self._iid_to_order.clear()
        self._genre_order.clear()
        self._genre_to_words.clear()
        self._word_to_genre.clear()
        self._sel_line = None

        self.text.configure(state="normal")
        self.text.delete("1.0", "end")

        grouped: Dict[str, List[Tuple[int, WordItem]]] = {}
        for idx, it in enumerate(items):
            grouped.setdefault(it.get("genre") or "(未分類)", []).append((idx, it))

        order_counter = 0
        line = 1
        for genre in sorted(grouped.keys()):
            gid = f"g:{genre}"
            self._genre_order.append(gid)
            self._genre_to_words.setdefault(genre, [])

            self.text.insert(f"{line}.0", genre + "\n", ("row::genre",))
            line += 1

            for idx, it in grouped[genre]:
                iid = f"w:{idx}"
                self._genre_to_words[genre].append(iid)
                self._word_to_genre[iid] = gid
                self._line_to_iid[line] = iid
                self._iid_to_line[iid] = line
                self._iid_to_order[iid] = order_counter
                order_counter += 1

                runs = it.get("word_runs")
                if isinstance(runs, list) and runs:
                    for seg in runs:
                        t = seg.get("text", "")
                        fg = seg.get("fg")
                        tag = f"fg::{fg}" if fg in ("red","blue") else "fg::default"
                        self.text.insert(f"{line}.end", t, (tag,))
                else:
                    self.text.insert(f"{line}.0", it.get("word",""), ("fg::default",))
                self.text.insert(f"{line}.end", "\n")
                line += 1

        self.text.configure(state="disabled")

        # select first word (no notify)
        first_word = None
        for gid in self._genre_order:
            g = gid[2:]
            ws = self._genre_to_words.get(g, [])
            if ws:
                first_word = ws[0]
                break
        if first_word:
            self._select_by_iid(first_word, notify=False)

    def select_by_id(self, idx_str: str) -> None:
        iid = idx_str if idx_str.startswith("w:") else f"w:{int(idx_str)}"
        self._select_by_iid(iid, notify=True)

    def _select_by_iid(self, iid: str, notify: bool) -> None:
        line = self._iid_to_line.get(iid)
        if line is None:
            return
        if self._sel_line is not None:
            self.text.tag_remove("row::sel", f"{self._sel_line}.0", f"{self._sel_line}.end")
        self._sel_line = line
        self.text.tag_add("row::sel", f"{line}.0", f"{line}.end")
        self.text.see(f"{line}.0")
        if notify and self.on_select_iid:
            try:
                self.on_select_iid(iid)
            except TypeError:
                pass

    def _line_from_y(self, y: int) -> Optional[int]:
        try:
            index = self.text.index(f"@0,{y}")
            ln = int(index.split(".")[0])
            return ln if ln in self._line_to_iid else None
        except Exception:
            return None

    def _on_click(self, evt=None):
        ln = self._line_from_y(evt.y if evt else 0)
        if ln is not None:
            self._select_by_iid(self._line_to_iid[ln], notify=True)

    def _on_move(self, evt=None):
        if self._sel_line is None:
            return "break"
        delta = -1 if (evt.keysym == "Up") else 1
        lines = sorted(self._line_to_iid.keys())
        try:
            i = lines.index(self._sel_line)
            ln = lines[max(0, min(len(lines)-1, i+delta))]
            self._select_by_iid(self._line_to_iid[ln], notify=True)
        except ValueError:
            pass
        return "break"

    def _on_edit(self, evt=None):
        # Ensure selection for double-click using event Y
        if (self._sel_line is None) and evt is not None:
            ln = self._line_from_y(evt.y)
            if ln is not None:
                self._select_by_iid(self._line_to_iid[ln], notify=False)

        if self._sel_line is None or self.on_edit_word is None:
            return
        iid = self._line_to_iid.get(self._sel_line)
        if not iid or not iid.startswith("w:"):
            return
        try:
            idx_int = int(iid.split(":",1)[1])
        except Exception:
            return

        # Prefer INT for main_panel._on_tree_edit_word
        for arg in (idx_int, str(idx_int), iid):
            try:
                self.on_edit_word(arg)  # type: ignore
                return
            except TypeError:
                continue
