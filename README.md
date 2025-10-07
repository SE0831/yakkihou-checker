# 薬機・景表チェッカー (Yakkihou Checker)

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.39+-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

広告文を解析し、**薬機法/景品表示法**の観点で要注意表現を検出するツールです。  
FastAPI で API、Streamlit で **日本語UI** を提供します。

---

## 主な機能

- YAMLルールに基づく NG 表現検出  
  （例：絶対表現 / 医薬品的効能の断定 / 過度な期間短縮 / 根拠不明 など）
- スコア算出・検出一覧（表 / カード）・**テキストハイライト**
- 結果を **CSV ダウンロード**（BOM付き UTF-8）
- Swagger UI (`/docs`) で API 試験可能

---

## デモ画面

`docs/screenshot-ui.png` を参照（任意）

---

## 技術スタック

- Python 3.11+
- FastAPI / Uvicorn
- Streamlit
- Ruff / mypy / pytest

---

## セットアップ

ローカル環境で動かす場合の手順です。

```bash
git clone https://github.com/<YOUR_ACCOUNT>/yakkihou-checker.git
cd yakkihou-checker
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

## 実行方法

### APIサーバーを起動（ターミナルA）

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
# → http://127.0.0.1:8000/docs にアクセスすると Swagger UI が開きます

source .venv/bin/activate
streamlit run ui/app.py
# → http://127.0.0.1:8501 にアクセスすると UI が開きます
