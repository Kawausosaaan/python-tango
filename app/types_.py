# app/types_.py
from typing import Dict, List, Optional, TypedDict


# 1 run = {"text": str, "color": "red"|"blue"|""}
class TextRun(TypedDict):
    text: str
    color: str  # "red" | "blue" | ""（黒）


# 既存互換: word/meaning は従来の文字列のままでもOK
WordItem = Dict[str, object]  # keys: "word": str, "meaning": str, "genre"?: str,
#       "word_runs"?: List[TextRun], "meaning_runs"?: List[TextRun]
