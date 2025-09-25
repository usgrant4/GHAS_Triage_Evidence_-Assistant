import os
import time
import json
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
                # Corrected API call and response parsing
                resp = self.client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": json.dumps(user)}
                    ],
                    response_format={"type": "json_object"},
                    timeout=TIMEOUT,
                )
                # Extract the JSON content from the modern response structure
                content = resp.choices[0].message.content
                if content:
                    return json.loads(content)

                raise RuntimeError("OpenAI response was empty.")
            except Exception as e:
                print(f"OpenAI API call failed with error: {e}")

                if "insufficient_quota" in str(e).lower():
                    raise
                time.sleep(backoff)
        
        raise RuntimeError("LLM call failed after retries")