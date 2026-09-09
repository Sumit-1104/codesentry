from dotenv import load_dotenv
import os
from openai import OpenAI

# .env file se API key load karo
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("❌ Groq API key nahi mili. .env file check kar.")
else:
    print("✅ API key mil gayi, ab Groq ko call kar rahe hai...")
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
       max_tokens=5000,
        messages=[{"role": "user", "content": "Bas 'Setup successful!' bol de, aur kuch nahi."}]
    )
    
    print("Model ka jawab:", response.choices[0].message.content)