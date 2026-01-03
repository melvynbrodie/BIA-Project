
import google.generativeai as genai
import os
from app.core.config import settings

# Configure API
genai.configure(api_key=settings.GEMINI_API_KEY)

def list_models():
    try:
        print("Listing available models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model: {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
