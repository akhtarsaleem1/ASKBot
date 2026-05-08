import os
import requests
import base64
import logging
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

load_dotenv("d:\\Software\\ASKBot\\.env")

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

# Improved prompt from image_generator.py
prompt = (
    "High-end, professional app store marketing hero image for 'ASK Fitness'. "
    "Subject: A creative and premium visual metaphor for 'Daily Fitness tracking'. "
    "Style: Minimalist 3D render, Apple-style aesthetics, clean and sophisticated. "
    "Visual elements: Abstract flowing shapes, soft studio lighting, premium materials (glass, matte metal, glowing neon), "
    "vibrant but harmonious tech gradient background, deep depth of field with soft bokeh. "
    "Composition: 1:1 square, cinematic wide-angle perspective. "
    "Important: Keep the left side relatively clean/uncluttered for text overlay. "
    "Negative Constraints: No people, no phones, no devices, no realistic hands, no text, no letters, no logos, "
    "no watermarks, no messy details, no unprofessional artifacts, no cartoonish styles."
)

url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {
        "responseModalities": ["IMAGE"],
        "temperature": 0.9,
    },
}

print(f"Testing with model: {model}")
try:
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=120)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            found = False
            for part in parts:
                if "inlineData" in part:
                    print("Success: Found image data!")
                    raw = base64.b64decode(part["inlineData"]["data"])
                    img = Image.open(BytesIO(raw))
                    img.save("scratch/test_premium.png")
                    print("Image saved to scratch/test_premium.png")
                    found = True
                    break
            if not found:
                print("No image data in parts:", parts)
        else:
            print("No candidates:", data)
    else:
        # If Gemini fails, test Pollinations fallback with the same prompt
        print(f"Gemini failed ({response.status_code}). Testing Pollinations fallback...")
        pollinations_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?nologo=true&enhance=true"
        resp = requests.get(pollinations_url, timeout=30)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            img.save("scratch/test_pollinations_fallback.png")
            print("Pollinations fallback image saved to scratch/test_pollinations_fallback.png")
        else:
            print(f"Pollinations fallback failed: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")
