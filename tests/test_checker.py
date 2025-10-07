from app.nlp.checker import analyze_text

def test_detects_absolute():
    res = analyze_text("これは絶対に効果があります")
    labels = [s["label"] for s in res["spans"]]
    assert "絶対表現" in labels
    assert res["score"] > 0
