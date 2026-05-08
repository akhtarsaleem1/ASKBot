from fastapi.testclient import TestClient
from askbot.main import app

client = TestClient(app)

print("Testing /history...")
try:
    response = client.get("/history")
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(response.text[:1000])
except Exception as e:
    print(f"Error: {e}")

print("\nTesting /preview...")
try:
    response = client.get("/preview")
    print(f"Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting /analytics...")
try:
    response = client.get("/analytics")
    print(f"Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting /gallery...")
try:
    response = client.get("/gallery")
    print(f"Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
