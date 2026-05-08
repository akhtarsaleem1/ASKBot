import requests
from dotenv import load_dotenv
import os

load_dotenv("d:\\Software\\ASKBot\\.env")
API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response

output = query({
    "inputs": "A professional AI logo, minimalist, 3D",
})
print(f"Status: {output.status_code}")
print(f"Content-Type: {output.headers.get('Content-Type')}")
if output.status_code == 200:
    print("Success!")
    with open("scratch/generated_test.png", "wb") as f:
        f.write(output.content)
else:
    print(output.text)
