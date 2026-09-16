from dotenv import load_dotenv
import os
import time
from openai import OpenAI
from rag.embedder import search_similar_code

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def generate_tests(filepath):
    """
    Ye function ek Python file padhta hai, RAG se related context nikalta hai,
    aur Groq LLM ko bhejta hai taaki wo pytest ke format mein unit tests likhe.
    Rate limit hit hone pe automatically retry karta hai.
    """
    
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()
    
    related = search_similar_code(f"code related to: {code[:200]}", n_results=2)
    context = "\n".join(related["documents"][0]) if related["documents"] else ""
    
    prompt = f"""Ye Python code dekho:

{code}

Yaha kuch related code hai poore codebase se, context ke liye:
{context}

Is code ke functions ke liye pytest unit tests likho.
Har function ke liye kam se kam 2 test cases banao:
1. Normal/expected input ke liye
2. Edge case (jaise zero, negative number, ya khaali input) ke liye

Sirf wahi cross-reference mention karo jo related context mein explicitly dikh raha ho.
Sirf test code do, explanation mat do. pytest format use karo (assert statements ke saath).
"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                max_tokens=2000,
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


if __name__ == "__main__":
    tests = generate_tests("data/sample_code.py")
    print(tests)