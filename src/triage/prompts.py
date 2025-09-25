SYSTEM_PROMPT = (
    "You are a security triage assistant. "
    "For each finding, return JSON list 'items' where each item has: "
    "rule_id, file, start_line, owasp_category, cwe_id, severity (low|medium|high|critical), "
    "exploitability (1-5), remediation_steps (list), developer_comment, evidence_snippet."
)

def build_user_payload(findings: list[dict]) -> dict:
    # Keep request compact
    slim = []
    for f in findings:
        slim.append({
            "rule_id": f["rule_id"],
            "message": f["message"][:240],
            "file": f["file"],
            "start_line": f["start_line"],
            "code_snippet": (f.get("code_snippet") or "")[:240]
        })
    return {"findings": slim}
