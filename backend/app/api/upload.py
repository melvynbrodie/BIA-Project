
from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.services.ingestion import save_upload_file, process_filing
from app.models.schema import Filing, Company # Need a DB dependency helper
from app.core.config import settings
# Mock DB dependency
def get_db():
    yield None 

router = APIRouter()

@router.post("/upload")
async def upload_filing(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    company_id: str | None = Form(None),
    period: str | None = Form(None)
):
    print(f"DEBUG: Received upload request. File: {file.filename}, Company: {company_id}")
    # 1. Identify Company (Optimized for Free Tier)
    # Critical Optimization: Trust the user-provided company_id first to avoid heavy AI processing on upload
    # This prevents timeouts (Vercel 10s limit) and OOMs (Render 512MB limit)
    detected_company_id = None
    
    if company_id and company_id != "undefined" and len(company_id) > 2:
        print(f"DEBUG: Using provided company_id: {company_id}")
        detected_company_id = company_id
    else:
        # Fallback to AI only if absolutely necessary
        try:
            import pdfplumber
            from app.services.gemini import generate_content
            
            # Read LESS pages (only 2) to save RAM
            text_preview = ""
            with pdfplumber.open(file.file) as pdf:
                for page in pdf.pages[:2]: 
                    text_preview += page.extract_text() or ""
            
            file.file.seek(0)
            
            if len(text_preview) > 50:
                prompt = f"""Identify the NSE Ticker (e.g. INFY, TCS) from this text. Return JSON {{ "ticker": "SYMBOL" }}. Text: {text_preview[:1000]}"""
                response = await generate_content(prompt)
                # ... simple extract ...
                 
                import json, re
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                   detected_company_id = json.loads(json_match.group(0)).get("ticker")

        except Exception as e:
            print(f"AI Detection skipped/failed: {e}")
            detected_company_id = "UNKNOWN"

    if not detected_company_id:
        detected_company_id = "UNKNOWN_COMPANY"

    # 2. Save file with DETECTED ID
    try:
        file_path = save_upload_file(file, detected_company_id)
    except Exception as e:
        print(f"File Save Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    
    # 3. Trigger processing in BACKGROUND to prevent timeout
    # Charts (Yahoo) will load immediately. Chatbot (PDF) will be ready in ~1 min.
    try:
        background_tasks.add_task(process_filing, file_path, detected_company_id, 1, None)
    except Exception as e:
        print(f"Background Task Error: {e}")
    
    return {"message": "File uploaded. Processing in background.", "company_id": detected_company_id, "path": str(file_path)}
