from pathlib import Path
from typing import Any, Dict, List
import regex as re
import yaml

class RuleEngine:
    def __init__(self, rules_path: str):
        data = yaml.safe_load(Path(rules_path).read_text(encoding="utf-8"))
        self.patterns = []
        for p in data["patterns"]:
            p["compiled"] = re.compile(p["regex"], re.IGNORECASE | re.MULTILINE)
            self.patterns.append(p)

    def analyze(self, text: str) -> Dict[str, Any]:
        spans: List[Dict[str, Any]] = []
        risk = 0
        for p in self.patterns:
            for m in p["compiled"].finditer(text):
                spans.append({
                    "start": m.start(),
                    "end": m.end(),
                    "matched": m.group(0),
                    "rule_id": p["id"],
                    "label": p["label"],
                    "law": p["law"],
                    "severity": p["severity"],
                    "suggest": p.get("suggest", ""),
                    "note": p.get("note", ""),
                })
                risk += {"high": 3, "mid": 2, "low": 1}.get(p["severity"], 1)
        return {
            "score": min(100, risk * 5),
            "spans": spans,
            "meta": {"rules_count": len(self.patterns)},
        }

_engine = RuleEngine("app/nlp/rules/ng_rules.yml")

def analyze_text(text: str) -> Dict[str, Any]:
    return _engine.analyze(text)
