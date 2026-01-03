
import asyncio
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load env from .env file
load_dotenv(dotenv_path=".env")

API_KEY = os.getenv("GEMINI_API_KEY")
print(f"Checking API Key: {'Found' if API_KEY else 'Missing'}")

genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-2.0-flash"

async def test_gemini():
    print(f"Testing model: {MODEL_NAME}")
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = await model.generate_content_async("Hello, what is the ticker for Apple Inc?")
        print(f"Response: {response.text}")
        print("SUCCESS: Gemini API is working.")
    except Exception as e:
        print(f"FAILURE: Gemini API Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
