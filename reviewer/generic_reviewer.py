from dotenv import load_dotenv
import os
import time
import json
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def generate_structured_review(filepath):
    """
    Ye function kisi bhi language ki file ko LLM se review karwata hai,
    aur STRUCTURED JSON format mein line-level issues maangta hai
    (taaki Python files jaisa hi line-highlighting ho sake).
    """

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
    except Exception as e:
        return {"summary": f"Could not read file: {str(e)}", "issues": []}

    if len(code) > 6000:
        code = code[:6000] + "\n... (truncated)"

    if not code.strip():
        return {"summary": "File is empty, nothing to review.", "issues": []}

    prompt = f"""Ye code file dekho (line numbers 1 se shuru hote hai):

{code}

Is code ka review karo aur SIRF valid JSON return karo, is exact format mein
(koi extra text, koi markdown fences, sirf raw JSON):

{{
  "summary": "1-2 line overall summary of the file",
  "issues": [
    {{"line": 5, "message": "short description of the issue", "severity": "warning"}},
    {{"line": 12, "message": "short description", "severity": "danger"}}
  ]
}}

severity hamesha "info", "warning", ya "danger" mein se ek ho
(danger = security/critical, warning = code quality, info = style/minor).
Max 6 issues do, sirf sabse important wale. Agar file clean hai, "issues" khaali list ["]  do.
"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                max_tokens=1500,
                reasoning_effort="low",
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.choices[0].message.content.strip()

            # Kabhi kabhi LLM ```json fences daal deta hai, unhe hata do
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            data = json.loads(raw)
            return {
                "summary": data.get("summary", ""),
                "issues": data.get("issues", [])
            }
        except json.JSONDecodeError:
            return {"summary": raw if 'raw' in dir() else "Could not parse review.", "issues": []}
        except Exception as e:
            error_str = str(e).lower()
            if "tokens per day" in error_str or "tpd" in error_str:
                return {"summary": "Daily API quota exhausted. Try again tomorrow.", "issues": []}
            elif "rate_limit" in error_str and attempt < max_retries - 1:
                time.sleep(15)
            else:
                return {"summary": f"Could not analyze this file: {str(e)}", "issues": []}

    return {"summary": "Analysis failed after retries.", "issues": []}