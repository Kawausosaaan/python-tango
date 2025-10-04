# プロジェクト名
- python-tango

## 目的（1–3行）
- 単語帳GUIアプリ。CSVを読み込み、A/Dで前後移動、Fで詳細表示、Sで保存。

## 入口（どう起動する？）
- `python -m app`

## 動作環境
- Python: 3.10.6（`python --version` で確認）
- OS: Windows 11
- 主要ライブラリ: Tkinter など

## セットアップ

### 0) 前提
- Python 3.10 以上
- （任意）Git / SourceTree

### 1) リポジトリ取得
**A. 既存フォルダから始める（現在の方法）**  
1. SourceTree → **[ファイル] > [追加]** でプロジェクトフォルダを選択  
2. **[リポジトリを作成]**（未初期化なら）でGit初期化  
3. 必要なら **.gitignore** を作成（`*.pyc`, `__pycache__/`, `.venv/`, `.env` など）  
4. `README.md`, `requirements.txt`, `config.sample.json` をコミット  
5. リモートに上げる場合（任意）：**[リポジトリ] > [リモートを追加]** → URL設定 → **[プッシュ]**  

**B. リモート（URL）からクローン**  
1. SourceTree → **[新規] > [URL からクローン]**  
2. ソースURL入力 → 保存先選択 → **[クローン]**

### 2) 仮想環境を用意（※未作成ならこの手順で作成）
**Windows (PowerShell)**
```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1   # 有効化（プロンプトに (.venv) と出ればOK）
