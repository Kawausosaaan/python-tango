# app/main.py
from __future__ import annotations

from typing import List

from main_panel import MainPanel
from types_ import WordItem
from word_repository import WordRepository


def main() -> None:
    repo = WordRepository()
    loaded = repo.load()
    initial_words: List[WordItem] = [
        {"word": "apple", "meaning": "りんご", "genre": "食べ物/果物"},
        {"word": "book", "meaning": "本", "genre": "学校/道具"},
        {"word": "computer", "meaning": "コンピュータ", "genre": "IT/機器"},
    ]
    MainPanel(loaded or initial_words).run()


if __name__ == "__main__":
    main()
