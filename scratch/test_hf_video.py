import os
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv("d:\\Software\\ASKBot\\.env")

api_key = os.getenv("HUGGINGFACE_API_KEY")
# CogVideoX-5b is a common model for video generation
model = "THUDM/CogVideoX-5b"

client = InferenceClient(api_key=api_key)

prompt = (
    "Cinematic 9:16 vertical video. A futuristic AI assistant glowing orb floating in a minimalist Apple-style studio. "
    "Soft bokeh, professional studio lighting, high resolution, detailed texture."
)

print(f"Generating video with model: {model} using InferenceClient...")
try:
    # CogVideoX-5b might take a while, and serverless might not support it for free
    # Let's see if it works or if it requires a provider
    video_bytes = client.text_to_video(prompt, model=model)
    with open("scratch/test_video.mp4", "wb") as f:
        f.write(video_bytes)
    print("Success: Video saved to scratch/test_video.mp4")
except Exception as e:
    print(f"Error: {e}")
