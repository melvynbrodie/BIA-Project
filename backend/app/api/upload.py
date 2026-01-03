
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
    company_id: str = Form(...),
    period: str = Form(...)
):
    print(f"DEBUG: Received upload request. File: {file.filename}, Company: {company_id}")
    # 1. Identify Company from File Content (First 2 Pages)
    detected_company_id = None
    try:
        import pdfplumber
        from app.services.gemini import generate_content
        
        # Read first 5 pages for better coverage
        text_preview = ""
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages[:5]: 
                text_preview += page.extract_text() or ""
        
        # Reset file cursor for saving later
        file.file.seek(0)
        
        # Suppress pdfminer logs
        import logging
        logging.getLogger('pdfminer').setLevel(logging.ERROR)
        
        if len(text_preview) > 50:
            prompt = f"""
            Task: Identify the Publicly Listed NSE Ticker for this Annual Report.
            
            1. Analyze the text below (First 5 pages extracted).
            2. Identify the specific company (e.g., "Tata Motors", "Infosys", "Reliance Industries").
            3. Return the EXACT NSE Ticker Symbol in JSON format.
            
            Key Rules:
            - If it mentions "Tata", find WHICH Tata company (TATAMOTORS, TATASTEEL, TCS, TATACHEM).
            - If it mentions "Adani", find WHICH Adani company (ADANIENT, ADANIPORTS).
            
            Output format: JSON ONLY.
            {{ "ticker": "SYMBOL" }}
            
            Example:
            {{ "ticker": "INFY" }}
            {{ "ticker": "TATAMOTORS" }}

            TEXT START:
            {text_preview[:4000]}
            """
            response = await generate_content(prompt)
            print(f"DEBUG GEMINI RAW RESPONSE: {response}")
            
            import json
            import re
            
            # Extract JSON from response (handle potential markdown blocks)
            try:
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                    candidate = data.get("ticker", "").upper().replace(".NS", "").replace(".BO", "").strip()
                else:
                    # Fallback to legacy split if no JSON found
                    candidate = response.strip().split()[0].upper().replace(".NS", "").replace(".BO", "").replace(".", "")
            except:
                candidate = "UNKNOWN"

            # Simple validation: Tickers are usually 3-15 chars, alphabetic
            if len(candidate) >= 3 and len(candidate) < 20 and candidate.isalpha():
                print(f"Detected Company Ticker: {candidate}")
                detected_company_id = candidate
            else:
                print(f"AI returned invalid ticker: {candidate}")
            
    except Exception as e:
        print(f"Company Detection Error: {e}")
        import traceback
        traceback.print_exc()
    # Critical: If detection failed, use the provided company_id as fallback
    if not detected_company_id:
        print(f"DEBUG FAILURE: Text length was {len(text_preview)}")
        print(f"DEBUG FAILURE: Preview: {text_preview[:200]}")
        
        # Fallback to the manual input if AI fails
        if company_id and company_id != "undefined":
            print(f"Falling back to provided company_id: {company_id}")
            detected_company_id = company_id
        else:
            raise HTTPException(status_code=400, detail="Could not automatically identify the company and no company ID was provided. Please ensure the PDF has text.")

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
