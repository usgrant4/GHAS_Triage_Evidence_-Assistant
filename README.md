# GHAS Triage & Evidence Assistant

A practical DevSecOps helper that ingests GitHub Advanced Security (GHAS) **SARIF** results and produces:
- Consistent risk triage (severity, exploitability, rationale)
- OWASP + CWE tagging
- Concise, PR‑ready developer guidance
- Audit‑friendly compliance evidence (e.g., NIST ISO‑style language)
- A single “sticky” PR comment that stays updated on each run

This project is designed to be **fast, inexpensive, and unobtrusive**. It processes only the minimum SARIF fields needed, deduplicates findings, batches prompt calls, and posts a compact summary to the PR while storing full details as artifacts efficiently.


## Why this exists

Security teams and developers face three recurring problems:
1. **Noise**: dozens of similar findings with different file paths drown out real risk.
2. **Inconsistency**: ad‑hoc remediation text varies in clarity and usefulness.
3. **Evidence gaps**: audits need policy‑aligned language tied to real findings.

This assistant centralizes triage and evidence into a repeatable, low‑friction workflow.


## Features

- **CLI**: Process SARIF locally to JSON and Markdown.
- **FastAPI**: Optional REST service for CI systems or other tools.
- **GitHub Action**: Post or update a single sticky PR comment summarizing top issues; attach a full triage report as an artifact.
- **OWASP/CWE labeling**: Lightweight rubric‑prompting for consistent tags.
- **Compliance evidence**: Generates plain‑language evidence snippets per finding that you can paste into audit folders.
- **Cost controls**: Batching, field truncation, top‑N filtering, and model tiering.
- **Deterministic behavior**: Stable finding fingerprints and cache to avoid re‑processing.


## Quick start (Windows 10/11 + PowerShell)

```powershell
# 1) Clone and open
git clone https://github.com/YOUR-ORG/ghas-triage-assistant.git
cd ghas-triage-assistant

# 2) Create venv and install
python -m venv .venv; . .\.venv\Scripts\Activate; python -m pip install --upgrade pip; pip install -e .

# 3) Configure secrets (local dev)
Copy-Item .env.example .env; notepad .env
# Set OPENAI_API_KEY=sk-... (and optional settings below)

# 4) Run CLI against a SARIF file
python -m triage.cli sarif\sample.sarif --out_json triage.json --out_md triage.md

# 5) Run API locally (optional)
uvicorn app.main:app --reload
```

macOS/Linux differences:
```bash
python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip && pip install -e .
cp .env.example .env && $EDITOR .env
python -m triage.cli sarif/sample.sarif --out_json triage.json --out_md triage.md
uvicorn app.main:app --reload
```


## Configuration

Create a `.env` file (never commit it).

```
# OpenAI (default: OpenAI public API)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SEC=30

# Batching and token controls
TRIAGE_TOP_N=50             # max findings to triage per run (after dedupe/sort)
TRIAGE_BATCH_SIZE=20        # findings per LLM call batch
SNIPPET_MAX_CHARS=240       # truncate code/context to reduce tokens
EVIDENCE_STYLE=nist         # nist|iso|plain

# Optional: Azure OpenAI
# AZURE_OPENAI_KEY=...
# AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com/
# AZURE_OPENAI_API_VERSION=2024-08-01-preview
# OPENAI_API_TYPE=azure
# OPENAI_MODEL=gpt-4o-mini    # your deployed model name
```

Model choice:
- Default is `gpt-4o-mini` for price/performance.
- You can set `OPENAI_MODEL=gpt-4.1` (or another) when you need richer reasoning.
- The tool will prefer **small → large** escalation only for ambiguous items when enabled.


## How it works

1. **Parse SARIF**: Extract compact fields
   - `ruleId`, `ruleDescription`
   - `file`, `startLine`
   - `message` (truncated)
   - `codeSnippet` (optional, truncated)
2. **Fingerprint findings**:
   - `fingerprint = sha256(f"{ruleId}|{file}|{startLine}|{message[:120]}")`
3. **Dedupe and sort**:
   - Collapse duplicates by `ruleId + file + line`
   - Sort: `Critical → High → Medium → Low`, then by rule grouping
4. **Batch prompts**:
   - Send only top‑N finding tuples in batches (`TRIAGE_BATCH_SIZE`), no codeflows or heavy metadata
5. **LLM output (JSON)**:
   - For each finding: `{ owasp, cwe, severity, exploitability(1‑5), remediation, developer_comment, evidence }`
6. **Artifacts**:
   - `triage.json` (full) and `triage.md` (human summary)
7. **Sticky PR comment**:
   - A short table of top risks, link to the full artifact, and a hidden marker to update in place.


## GitHub Action (PR workflow)

`.github/workflows/triage.yml`
```yaml
name: GHAS Triage
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  security-events: read

jobs:
  triage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install
        run: |
          python -m pip install --upgrade pip
          pip install -e .

      - name: Download latest SARIF (if any)
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: not_present.sarif
        continue-on-error: true

      - name: Find SARIF path
        id: find_sarif
        shell: bash
        run: |
          CANDIDATES=$(git ls-files '**/*.sarif' | head -n 1 || true)
          if [ -z "$CANDIDATES" ]; then
            echo "sarif_path=" >> $GITHUB_OUTPUT
          else
            echo "sarif_path=$CANDIDATES" >> $GITHUB_OUTPUT
          fi

      - name: Generate triage
        if: always()
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python -m triage.cli "${{ steps.find_sarif.outputs.sarif_path || 'sarif/sample.sarif' }}" --out_json triage.json --out_md triage.md

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ghas-triage
          path: |
            triage.json
            triage.md

      - name: Post or update sticky comment
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python -m triage.sticky_comment triage.md
```

Notes:
- If you rely on **Code Scanning** workflows, schedule this job **after** they run (or use `workflow_run` targeting your scanning workflow). The PR‑triggered approach above works when your scanning workflow runs on PRs.


## CLI usage

```
python -m triage.cli <sarif_path> [--out_json triage.json] [--out_md triage.md]
```

Example:
```
python -m triage.cli sarif/sample.sarif --out_json out/triage.json --out_md out/triage.md
```

Outputs:
- `triage.json`: machine‑readable results
- `triage.md`: developer summary with top risks and remediation bullets


## API usage (FastAPI)

```
POST /triage
Content-Type: multipart/form-data
file: <SARIF file>
```

Response:
```json
{
  "triage": { "items": [ /* per finding results */ ] },
  "markdown": "## Summary ..."
}
```


## Sticky PR comment behavior

- The comment includes a hidden marker: `<!-- ghas-triage-sticky -->`.
- On each run, the action looks for this marker:
  - If found, it updates the existing comment.
  - If not, it creates a new comment.
- The comment shows top issues and links the full artifact.


## Performance and cost controls

- **Field minimization**: only the smallest useful finding tuple is sent.
- **Truncation**: `SNIPPET_MAX_CHARS` reduces token usage.
- **Top‑N**: cap with `TRIAGE_TOP_N`. For large PRs, this keeps costs predictable.
- **Batching**: `TRIAGE_BATCH_SIZE` controls per‑request payload size.
- **Tiered models**: default to `gpt-4o-mini`; only escalate for ambiguous cases (optional flag).
- **Stable caching**: a `.triage_cache/` folder stores prior results keyed by `commit_sha + fingerprint` to avoid re‑calling the LLM for unchanged findings.
- **Backoff + retries**: transient 429s handled with exponential backoff; `insufficient_quota` surfaces clearly.
- **Concurrency cap**: batches are processed sequentially by default; toggle parallelism only if your account limits allow it.


## Security

- No secrets printed. Avoid logging raw prompts or outputs in CI.
- `.env` is excluded via `.gitignore`.
- The PR comment contains **no sensitive data** beyond what’s in SARIF.
- Optional redaction: the parser can mask common secrets patterns before prompt calls.


## Testing

```powershell
. .\.venv\Scripts\Activate; pytest -q
```

Included tests:
- `test_sarif.py`: parsing and truncation
- `test_prompts.py`: schema conformance for responses (JSON)
- `test_cli.py`: golden file tests for `triage.md`


## Troubleshooting

- **No SARIF found**: ensure your code scanning workflow uploads SARIF or commits SARIF fixtures in the repo.
- **OPENAI_API_KEY not set**: set in GitHub Secrets (`OPENAI_API_KEY`) and in local `.env` for dev.
- **429 insufficient_quota**: add billing or switch to a smaller model; reduce `TRIAGE_TOP_N` / `BATCH_SIZE`.
- **pip not recognized (Windows)**: open a new terminal after install or use `python -m pip ...`.
- **VS Code doesn’t see env var**: restart VS Code after `setx`, or load from `.env`.


## Project structure

```
src/
  triage/
    __init__.py
    models.py          # Pydantic types (FindingIn, FindingOut, BatchResult)
    sarif.py           # Minimal SARIF loader and truncation
    prompts.py         # Prompt templates and JSON schema
    openai_client.py   # Thin client with backoff and response_format=json
    cache.py           # Commit+fingerprint cache to avoid repeat calls
    evidence.py        # Evidence block builders (nist|iso|plain)
    cli.py             # Typer CLI entrypoint
    sticky_comment.py  # Upsert logic with hidden marker
  app/
    main.py            # FastAPI app
tests/
.github/workflows/triage.yml
.env.example
pyproject.toml
README.md
```


## Design rationale and effectiveness

- **Signal over noise**: dedupe by rule + location and group similar items for a clearer top list.
- **Developer‑first output**: short, actionable remediation bullets and a single PR comment reduce context switching.
- **Audit‑ready**: evidence text uses neutral, control‑aligned language so it can be dropped into control narratives.
- **Safe defaults**: small model, capped batches, and truncation keep cost and latency low by default.
- **Escape hatches**: environment variables allow quick tuning per repo without code changes.


## Roadmap (optional)

- JIRA/Azure Boards integration for auto‑tickets on Critical/High items.
- Branch policies: fail PR if Critical findings exceed a threshold.
- Organization‑level policy pack mapping.
- Azure deployment (Functions or Container Apps) for the API service.

## License

MIT

---

**Ulysses Grant, IV**  
[LinkedIn](https://www.linkedin.com/in/usgrant4/) 
[GitHub](https://github.com/usgrant4)

---