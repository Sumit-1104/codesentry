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


def generate_docstrings(filepath):
    """
    Ye function ek Python file padhta hai, RAG se related context nikalta hai,
    aur Groq LLM ko bhejta hai taaki wo missing docstrings suggest kare.
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

Is code mein jitne bhi functions aur classes hai jinme docstring missing hai,
unke liye ek proper Python docstring likho (PEP 257 style).
Sirf wahi cross-reference mention karo jo related context mein explicitly dikh raha ho.
Agar context mein koi clear usage pattern nahi hai, toh koi cross-reference mat banao.
Sirf docstrings do, poora code repeat mat karo.
Format: pehle function/class ka naam batao, phir uska docstring.
"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                wait_time = 15
                print(f"Rate limit hit, waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise


if __name__ == "__main__":
    suggestions = generate_docstrings("data/sample_code.py")
    print(suggestions)