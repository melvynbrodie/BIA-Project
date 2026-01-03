
import google.generativeai as genai
from app.core.config import settings

# Configure API
genai.configure(api_key=settings.GEMINI_API_KEY)

# Defaults
MODEL_PRO = "gemini-2.0-flash" # Updated to available model
MODEL_FLASH = "gemini-2.0-flash-exp"
MODEL_EMBED = "text-embedding-004"

def get_model(model_name: str = MODEL_PRO):
    return genai.GenerativeModel(model_name)

async def generate_content(prompt: str, model_name: str = MODEL_PRO) -> str:
    model = get_model(model_name)
    
    # Retry logic for 429 Resource Exhausted
    import asyncio
    base_delay = 2
    for attempt in range(4):
        try:
            response = await model.generate_content_async(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "Resource exhausted" in str(e):
                if attempt == 3:
                     raise e
                print(f"Gemini 429 Rate Limit. Retrying in {base_delay}s...")
                await asyncio.sleep(base_delay)
                base_delay *= 2
            else:
                print(f"Error generating content with {model_name}: {e}")
                raise e
    return "Error: Could not generate content."

async def generate_embeddings(text: str, model_name: str = MODEL_EMBED):
    try:
        result = genai.embed_content(
            model=model_name,
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        raise e
