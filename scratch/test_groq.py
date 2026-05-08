import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv("d:\\Software\\ASKBot\\.env")

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

client = Groq(api_key=api_key)

print(f"Testing Groq with model: {model}...")
try:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say hello",
            }
        ],
        model=model,
    )
    print(f"Success: {chat_completion.choices[0].message.content}")
except Exception as e:
    print(f"Error: {e}")
