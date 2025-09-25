import os, time, json
from typing import Dict, Any
from openai import OpenAI
from .prompts import SYSTEM_PROMPT, build_user_payload

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TIMEOUT = int(os.getenv("OPENAI_TIMEOUT_SEC", "30"))

class LLM:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        self.client = OpenAI(api_key=api_key)

    def classify_and_remediate(self, findings: list[dict]) -> Dict[str, Any]:
        user = build_user_payload(findings)
        for backoff in [1, 2, 4]:
            try:
                resp = self.client.responses.create(
                    model=MODEL,
                    input=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": json.dumps(user)}
                    ],
                    response_format={"type": "json_object"},
                    timeout=TIMEOUT,
                )
                # SDK returns a rich object; extract text safely
                text = getattr(resp, "output_text", None) or getattr(resp, "content", None)
                if hasattr(resp, "to_dict"):
                    data = resp.to_dict()
                    # Try to find JSON in top-level or text content
                    if isinstance(text, str):
                        try:
                            return json.loads(text)
                        except Exception:
                            pass
                    # Fall back to generic mapping
                    return data
                # If we only have text, parse JSON
                if isinstance(text, str):
                    return json.loads(text)
                raise RuntimeError("Unexpected response format from OpenAI.")
            except Exception as e:
                print(f"OpenAI API call failed with error: {e}")

                if "insufficient_quota" in str(e).lower():
                    raise
                time.sleep(backoff)
        raise RuntimeError("LLM call failed after retries")
