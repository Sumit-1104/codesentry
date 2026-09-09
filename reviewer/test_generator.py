from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


def generate_tests(filepath):
    """
    Ye function ek Python file padhta hai, aur Groq LLM ko bhejta hai
    taaki wo pytest ke format mein unit tests likhe.
    """
    
    with open(filepath, "r") as f:
        code = f.read()
    
    prompt = f"""Ye Python code dekho:

{code}

Is code ke functions ke liye pytest unit tests likho.
Har function ke liye kam se kam 2 test cases banao:
1. Normal/expected input ke liye
2. Edge case (jaise zero, negative number, ya khaali input) ke liye

Sirf test code do, explanation mat do. pytest format use karo (assert statements ke saath).
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content


if __name__ == "__main__":
    tests = generate_tests("data/sample_code.py")
    print(tests)