from pydantic import BaseModel, Field
from typing import List, Optional

class FindingIn(BaseModel):
    rule_id: str
    message: str
    file: str
    start_line: int
    code_snippet: Optional[str] = None

class FindingOut(BaseModel):
    rule_id: str
    file: str
    start_line: int
    owasp_category: str
    cwe_id: str
    severity: str
    exploitability: int = Field(ge=1, le=5)
    remediation_steps: List[str]
    developer_comment: str
    evidence_snippet: str

class BatchResult(BaseModel):
    items: List[FindingOut]
