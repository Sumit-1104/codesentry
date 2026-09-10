from dotenv import load_dotenv
import os
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
    """
    
    with open(filepath, "r") as f:
        code = f.read()
    
    # RAG se related code chunks dhoondo (poore codebase mein se)
    related = search_similar_code(f"code related to: {code[:200]}", n_results=2)
    context = "\n".join(related["documents"][0]) if related["documents"] else ""
    
    prompt = f"""Ye Python code dekho:

{code}

Yaha kuch related code hai poore codebase se, context ke liye:
{context}

Is code mein jitne bhi functions aur classes hai jinme docstring missing hai,
unke liye ek proper Python docstring likho (PEP 257 style).
Agar related context mein koi cross-reference relevant lage (jaise ye function kaha use ho raha hai),
toh docstring mein mention kar sakte ho.
Sirf docstrings do, poora code repeat mat karo.
Format: pehle function/class ka naam batao, phir uska docstring.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content


if __name__ == "__main__":
    suggestions = generate_docstrings("data/sample_code.py")
    print(suggestions)