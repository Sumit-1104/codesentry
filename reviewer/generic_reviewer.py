from dotenv import load_dotenv
import os
import time
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def generate_generic_review(filepath):
    """
    Ye function kisi bhi language ki file ko LLM se review karwata hai
    (Python ke alawa) - kyuki hamare paas har language ke liye alag
    static-analysis tool nahi hai, LLM khud reasoning se issues dhoondta hai.
    """
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
    except Exception as e:
        return f"Could not read file: {str(e)}"
    
    # Bahut badi files ko chhota kar do (token limit bachane ke liye)
    if len(code) > 6000:
        code = code[:6000] + "\n... (truncated)"
    
    if not code.strip():
        return "File is empty, nothing to review."
    
    prompt = f"""Ye code file dekho:

{code}

Is code ka language khud pehchano, aur ek code review do jisme:
1. Code quality issues (bad practices, unused code, naming issues)
2. Security concerns (agar koi ho, jaise hardcoded secrets, unsafe patterns)
3. Missing documentation/comments
4. Suggested test cases (agar applicable ho is language ke liye)

Concise raho, bullet points use karo. Agar file bahut simple/config file hai
(jaise JSON, CSS), toh sirf relevant sections do.
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
            return response.choices[0].message.content
        
        except Exception as e:
            error_str = str(e).lower()
            if "tokens per day" in error_str or "tpd" in error_str:
                # Daily limit khatam - retry karne ka koi fayda nahi, turant fail ho
                return "Daily API quota exhausted. Try again tomorrow, or upgrade your Groq plan."
            elif "rate_limit" in error_str and attempt < max_retries - 1:
                time.sleep(15)
            else:
                return f"Could not analyze this file: {str(e)}"
        