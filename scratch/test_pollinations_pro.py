import requests
from io import BytesIO
from PIL import Image

prompt = (
    "High-end, professional app store marketing hero image for an 'AI Assistant' app. "
    "Subject: A creative and premium visual metaphor for 'Conversational AI'. "
    "Style: Minimalist 3D render, Apple-style aesthetics, clean and sophisticated. "
    "Visual elements: Abstract glowing shapes, soft studio lighting, premium materials (glass, matte metal, glowing neon), "
    "vibrant tech gradient background, deep depth of field with soft bokeh. "
    "Composition: 1:1 square, cinematic wide-angle perspective. "
    "Negative Constraints: No people, no phones, no devices, no realistic hands, no text, no letters, no logos, "
    "no watermarks, no messy details, no unprofessional artifacts, no cartoonish styles."
)

# Use flux model on pollinations which is very high quality
url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?model=flux&nologo=true&enhance=true&width=1024&height=1024"

print("Generating high-quality image using Pollinations (Flux model)...")
try:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    image = Image.open(BytesIO(response.content)).convert("RGB")
    image.save("scratch/test_pollinations_premium.png")
    print("Success: Image saved to scratch/test_pollinations_premium.png")
except Exception as e:
    print(f"Error: {e}")
