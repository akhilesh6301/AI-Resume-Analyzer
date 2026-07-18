from google import genai
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(Path(__file__).parent / ".env")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

models = [
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
]

for model in models:
    print(f"\nTesting: {model}")
    try:
        response = client.models.generate_content(
            model=model,
            contents="Reply with only: Hello"
        )
        print("SUCCESS:", response.text)
        break
    except Exception as e:
        print("FAILED:", e)