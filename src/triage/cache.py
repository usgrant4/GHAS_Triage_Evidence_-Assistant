import hashlib, json, os
from typing import Dict

def fingerprint(f: Dict) -> str:
    base = f"{f['rule_id']}|{f['file']}|{f['start_line']}|{(f.get('message') or '')[:120]}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def ensure_cache_dir(path: str = ".triage_cache"):
    os.makedirs(path, exist_ok=True)
    return path
