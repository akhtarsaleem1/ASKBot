import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv
from PIL import Image

load_dotenv("d:\\Software\\ASKBot\\.env")

api_key = os.getenv("HUGGINGFACE_API_KEY")
model = os.getenv("HUGGINGFACE_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")

client = InferenceClient(api_key=api_key)

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

print(f"Generating professional image with model: {model}...")
try:
    image = client.text_to_image(prompt, model=model)
    image.save("scratch/generated_ai_app_pro.png")
    print("Success: Image saved to scratch/generated_ai_app_pro.png")
except Exception as e:
    print(f"Error: {e}")
