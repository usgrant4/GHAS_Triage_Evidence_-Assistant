from triage.sarif import load_sarif_findings
import json, os

def test_sarif_parse_sample(tmp_path):
    sample = {
        "runs": [{
            "tool": {"driver": {"rules": [{"id": "TEST001"}]}},
            "results": [{
                "ruleId": "TEST001",
                "message": {"text": "Hardcoded secret"},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": "src/app.py"},
                        "region": {"startLine": 10, "snippet": {"text": "key='abc'"}}
                    }
                }]
            }]
        }]
    }
    p = tmp_path / "sample.sarif"
    p.write_text(json.dumps(sample), encoding="utf-8")
    findings = load_sarif_findings(str(p))
    assert findings and findings[0]["rule_id"] == "TEST001"
