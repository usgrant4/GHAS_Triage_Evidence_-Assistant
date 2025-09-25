from typing import Dict, Any

def to_markdown(result: Dict[str, Any]) -> str:
    items = result.get("items") or result.get("triage", {}).get("items") or []
    if not items:
        return "### GHAS Triage\n\nNo findings."
    lines = ["### GHAS Triage Summary", "", "| Severity | Rule | Location | Note |", "|---|---|---|---|"]
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    items_sorted = sorted(items, key=lambda i: sev_order.get(i.get("severity","low").lower(), 3))
    for it in items_sorted[:20]:
        loc = f"{it.get('file','?')}:{it.get('start_line', '?')}"
        lines.append(f"| {it.get('severity','?').title()} | {it.get('rule_id','?')} | {loc} | {it.get('developer_comment','').replace('|','/')} |")
    lines.append("")
    lines.append("_Full triage details are available in the artifact (triage.json)._")
    return "\n".join(lines)
