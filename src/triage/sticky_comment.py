import os, subprocess, sys

MARKER = "<!-- ghas-triage-sticky -->"

def main(md_path: str):
    with open(md_path, "r", encoding="utf-8") as f:
        body = f.read()
    body = f"{MARKER}\n\n{body}"
    pr_number = os.environ.get("PR_NUMBER")

    # Use gh CLI to upsert. We search for the marker; if found, patch; else create.
    # This script assumes the GITHUB_TOKEN is configured for gh CLI already.
    try:
        # Get PR from env or fallback to latest open PR
        if not pr_number:
            pr_number = subprocess.check_output(
                ["gh", "pr", "list", "--state", "open", "--json", "number", "--jq", ".[0].number"],
                text=True
            ).strip()
        # Try to find existing comment id
        comment_id = subprocess.check_output(
            ["gh", "pr", "comments", pr_number, "--search", MARKER, "--json", "id", "--jq", ".[0].id"],
            text=True
        ).strip()
        if comment_id:
            subprocess.check_call(
                ["gh", "api", f"repos/${{GITHUB_REPOSITORY}}/issues/comments/{comment_id}", "-X", "PATCH", "-f", f"body={body}"]
            )
            print(f"Updated sticky comment {comment_id}")
            return
    except subprocess.CalledProcessError:
        pass

    # Create new comment
    subprocess.check_call(["gh", "pr", "comment", pr_number, "--body", body])
    print("Created sticky comment.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m triage.sticky_comment <triage.md>")
        sys.exit(1)
    main(sys.argv[1])
