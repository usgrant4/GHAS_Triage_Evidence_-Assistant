import json, os, typer
from dotenv import load_dotenv
from .sarif import load_sarif_findings
from .openai_client import LLM
from .evidence import to_markdown

app = typer.Typer(add_completion=False)

@app.command()
def sarif(path: str, out_json: str = "triage.json", out_md: str = "triage.md", top_n: int = 50):
    """Parse SARIF, call OpenAI, and write outputs."""
    load_dotenv()
    findings = load_sarif_findings(path)
    if not findings:
        typer.echo("No findings in SARIF.")
        with open(out_md, "w", encoding="utf-8") as f:
            f.write("### GHAS Triage\n\nNo findings.")
        return

    # Top-N trim
    findings = findings[: int(os.getenv("TRIAGE_TOP_N", top_n)) ]

    result = LLM().classify_and_remediate(findings)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(to_markdown(result))

    typer.echo(f"Wrote {out_json} and {out_md}")

if __name__ == "__main__":
    app()
