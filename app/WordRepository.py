# app/WordRepository.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

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

            # {"words": [...]} 形式にも対応
            if isinstance(raw, dict) and "words" in raw:
                raw = raw["words"]

            if not isinstance(raw, list):
                return []

            out: List[WordItem] = []
            for d in raw:
                if not isinstance(d, dict):
                    continue

                item: Dict[str, Any] = {
                    "word": str(d.get("word", "")),
                    "meaning": str(d.get("meaning", "")),
                }

                g = d.get("genre")
                if isinstance(g, str) and g:
                    item["genre"] = g

                # runs を素直に通す（存在すれば）
                for key in ("word_runs", "meaning_runs"):
                    v = d.get(key)
                    if isinstance(v, list):
                        cleaned = []
                        for r in v:
                            if not isinstance(r, dict):
                                continue
                            text = r.get("text")
                            if not isinstance(text, str):
                                continue
                            seg: Dict[str, Any] = {"text": text}

                            # 任意属性を安全にコピー（存在すれば）
                            if isinstance(r.get("fg"), str):
                                seg["fg"] = r["fg"]
                            if isinstance(r.get("bg"), str):
                                seg["bg"] = r["bg"]
                            if isinstance(r.get("bold"), bool):
                                seg["bold"] = r["bold"]
                            if isinstance(r.get("italic"), bool):
                                seg["italic"] = r["italic"]
                            if isinstance(r.get("underline"), bool):
                                seg["underline"] = r["underline"]

                            cleaned.append(seg)
                        if cleaned:
                            item[key] = cleaned

                out.append(item)
            return out
        except Exception:
            # 壊れたJSONなどは空配列を返す
            return []

    def save(self, words: List[WordItem]) -> None:
        """words をそのまま JSON へ保存（runs も含めて素直に保存）"""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                json.dump(words, f, ensure_ascii=False, indent=2)
            tmp.replace(self.path)
        except Exception:
            # 保存失敗時は黙って無視（必要ならログに変えてください）
            pass
