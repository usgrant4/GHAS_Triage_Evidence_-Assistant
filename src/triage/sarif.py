import json
from typing import List, Dict
from .models import FindingIn

def load_sarif_findings(path: str, snippet_max_chars: int = 240) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    runs = data.get("runs", [])
    for run in runs:
        tool = run.get("tool", {})
        rules = { r.get("id"): r for r in tool.get("driver", {}).get("rules", []) }
        for res in run.get("results", []):
            rule_id = res.get("ruleId", "unknown")
            msg = (res.get("message", {}) or {}).get("text", "")[:snippet_max_chars]
            locs = res.get("locations", []) or [{}]
            phys = (locs[0].get("physicalLocation") or {})
            art = (phys.get("artifactLocation") or {})
            file = art.get("uri", "UNKNOWN_FILE")
            region = phys.get("region") or {}
            start_line = int(region.get("startLine", 1))

            snippet = None
            if "snippet" in region:
                text = (region.get("snippet") or {}).get("text", "")
                snippet = text[:snippet_max_chars] if text else None

            results.append(FindingIn(
                rule_id=rule_id,
                message=msg,
                file=file,
                start_line=start_line,
                code_snippet=snippet
            ).model_dump())

    return results

def load_sarif_findings_from_bytes(data: bytes, snippet_max_chars: int = 240):
    obj = json.loads(data)
    tmp_path = "_tmp.sarif.json"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return load_sarif_findings(tmp_path, snippet_max_chars)
