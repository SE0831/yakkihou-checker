from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional  # ← 追加
from app.nlp.checker import analyze_text

# 入力モデル
class AnalyzeIn(BaseModel):
    text: str = Field(..., description="解析したいテキスト")

# 出力モデル
class Span(BaseModel):
    start: int = Field(..., description="一致開始位置")
    end: int = Field(..., description="一致終了位置")
    matched: str = Field(..., description="一致した文字列")
    rule_id: str = Field(..., description="適用されたルールID")
    label: str = Field(..., description="検出ラベル（例：絶対表現）")
    law: str = Field(..., description="対象法令（yakki / keihyo など）")
    severity: str = Field(..., description="重要度（high/mid/low）")
    suggest: Optional[str] = Field(None, description="言い換え候補")  # ← 修正
    note: Optional[str] = Field(None, description="補足メモ")          # ← 修正

class AnalyzeOut(BaseModel):
    score: int = Field(..., description="総合リスクスコア（0-100）")
    spans: List[Span] = Field(..., description="検出結果の一覧")
    meta: Dict[str, Any] = Field(..., description="メタ情報（ルール数など）")

app = FastAPI(
    title="薬機・景表チェッカー API",
    description="広告文を解析して、薬機法・景品表示法の観点で要注意表現を検出します。",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.post(
    "/api/analyze",
    summary="テキストを解析してNG/要注意表現を検出",
    response_model=AnalyzeOut,
    response_description="解析結果（スコアと検出箇所の一覧）"
)
def analyze(inp: AnalyzeIn) -> AnalyzeOut:
    return analyze_text(inp.text)

@app.get("/", summary="動作確認")
def root():
    return {"message": "薬機・景表チェッカーAPIは起動中です。/docs または /redoc を開いてください。"}
