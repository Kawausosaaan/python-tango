# app/WordRepository.py
from __future__ import annotations

import json
import traceback
from pathlib import Path
from typing import List, Optional

# 正: from .types_ import WordItem
from .types_ import WordItem


class WordRepository:
    """words.json をプロジェクト直下に保存/読込する"""

    def __init__(self, path: Optional[Path] = None) -> None:
        # app/ から見て1つ上（プロジェクト直下）の words.json をデフォルトに
        default = Path(__file__).resolve().parent.parent / "words.json"
        self.path = Path(path) if path else default

    def load(self) -> List[WordItem]:
        if not self.path.exists():
            return []
        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
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
            traceback.print_exc()
            return []

    def save(self, words: List[WordItem]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(words, f, ensure_ascii=False, indent=2)
            tmp.replace(self.path)
        except Exception:
            traceback.print_exc()
            return []
