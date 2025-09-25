from fastapi import FastAPI, UploadFile, File
from dotenv import load_dotenv
from triage.sarif import load_sarif_findings_from_bytes
from triage.openai_client import LLM
from triage.evidence import to_markdown

load_dotenv()
app = FastAPI(title="GHAS Triage Assistant")

@app.post("/triage")
async def triage(file: UploadFile = File(...)):
    data = await file.read()
    findings = load_sarif_findings_from_bytes(data)
    result = LLM().classify_and_remediate(findings)
    return {"triage": result, "markdown": to_markdown(result)}
