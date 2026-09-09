from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def generate_docstrings(filepath):
    """
    Ye function ek Python file padhta hai, aur Groq LLM ko bhejta hai
    taaki wo missing docstrings suggest kare.
    """
    
    # File ka poora content padho
    with open(filepath, "r") as f:
        code = f.read()
    
    # LLM ko prompt banao — usse specific instructions do
    prompt = f"""Ye Python code dekho:

{code}

Is code mein jitne bhi functions aur classes hai jinme docstring missing hai,
unke liye ek proper Python docstring likho (PEP 257 style).
Sirf docstrings do, poora code repeat mat karo.
Format: pehle function/class ka naam batao, phir uska docstring.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        max_tokens=5000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content


if __name__ == "__main__":
    suggestions = generate_docstrings("data/sample_code.py")
    print(suggestions)