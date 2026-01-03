
import os
import shutil
import json
import re
import csv
from pathlib import Path
import pdfplumber
from app.services.gemini import generate_embeddings, generate_content
from app.models.schema import DocumentChunk, Filing
from app.core.prompts import METRICS_EXTRACTION_PROMPT, VERIFICATION_PROMPT
from sqlalchemy.orm import Session

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

EXTRACTED_METRICS_DB = {} 
FULL_TEXT_DB = {} # Store raw text for RAG
VERIFICATION_SHEETS_DB = {} 

def save_upload_file(upload_file, company_ticker: str) -> Path:
    company_dir = UPLOAD_DIR / company_ticker
    company_dir.mkdir(exist_ok=True, parents=True)
    file_path = company_dir / upload_file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path

def extract_text_from_pdf(file_path: Path):
    text_content = []
    try:
        with pdfplumber.open(file_path) as pdf:
             # Extract first 50 pages + any pages mentioned in prompt if possible (hard to know before extraction)
             # Limiting to 250 for now
            pages_to_extract = pdf.pages[:250] 
            for i, page in enumerate(pages_to_extract):
                text = page.extract_text()
                if text:
                    content = f"[Page {i+1}]\n{text}"
                    text_content.append({"page": i + 1, "text": content})
    except Exception as e:
        print(f"Error extracting PDF: {e}")
    return text_content

def chunk_text(text_pages, chunk_size=1000, overlap=100):
    chunks = []
    current_chunk = ""
    current_meta = {"pages": []}
    
    for page in text_pages:
        page_text = page["text"]
        page_num = page["page"]
        
        if len(current_chunk) + len(page_text) > chunk_size * 4:
            chunks.append({"text": current_chunk, "metadata": current_meta})
            current_chunk = page_text[-overlap:]
            current_meta = {"pages": [page_num]}
        else:
            current_chunk += "\n" + page_text
            if page_num not in current_meta["pages"]:
                current_meta["pages"].append(page_num)
                
    if current_chunk:
        chunks.append({"text": current_chunk, "metadata": current_meta})
    return chunks

async def extract_financial_metrics(text_chunks, company_id, filename="Annual Report"):
    full_text = "\n".join([c["text"] for c in text_chunks])
    prompt = f"{METRICS_EXTRACTION_PROMPT}\n\n[CONTEXT DOCUMENT: {filename}]\n[TEXT_CONTENT]\n{full_text[:300000]}"
    
    try:
        response_text = await generate_content(prompt)
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            metrics = json.loads(json_match.group(0))
            return metrics, full_text
    except Exception as e:
        print(f"Metrics extraction failed: {e}")
        return None, full_text
    return None, full_text

async def verify_extraction(metrics, full_text, company_id):
    if not metrics: return
    
    # Send metrics + first 50k tokens (likely enough for verification)
    prompt = f"{VERIFICATION_PROMPT}\n\n[EXTRACTED JSON]\n{json.dumps(metrics, indent=2)}\n\n[SOURCE TEXT]\n{full_text[:50000]}"
    
    try:
        response_text = await generate_content(prompt)
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            verified_metrics = json.loads(json_match.group(0))
            verified_metrics["verified"] = True
            EXTRACTED_METRICS_DB[company_id] = verified_metrics
        else:
            metrics["verified"] = False
            EXTRACTED_METRICS_DB[company_id] = metrics
            
        # PERSISTENCE: Save metrics to file so it survives restart
        try:
            metrics_path = UPLOAD_DIR / company_id / "metrics.json"
            with open(metrics_path, "w") as f:
                json.dump(EXTRACTED_METRICS_DB[company_id], f, indent=2)
            print(f"Metrics saved to {metrics_path}")
        except Exception as e:
            print(f"Failed to save metrics.json: {e}")

    except Exception as e:
         print(f"Verification failed: {e}")
         metrics["verified"] = False
         EXTRACTED_METRICS_DB[company_id] = metrics

def generate_evidence_csv(file_path: Path, company_id: str, metrics: dict):
    """
    Finds page numbers from metrics citations and extracts tables from those pages.
    """
    if not metrics: return

    pages_to_extract = set()
    # Regex to find "Page X"
    for key in ["revenue", "operating_profit", "eps", "cash_flow", "roe"]:
        citation = metrics.get(key, {}).get("citation", "")
        if citation:
            match = re.search(r"Page\s(\d+)", citation, re.IGNORECASE)
            if match:
                try:
                     pages_to_extract.add(int(match.group(1)))
                except: pass

    evidence_data = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for page_num in pages_to_extract:
                if page_num <= len(pdf.pages):
                    page = pdf.pages[page_num - 1] 
                    tables = page.extract_tables()
                    
                    if tables:
                         evidence_data.append([f"--- TABLES FROM PAGE {page_num} ({metrics.get('revenue',{}).get('citation','')}) ---"])
                         for table in tables:
                             for row in table:
                                 evidence_data.append(row)
                             evidence_data.append([]) # Empty row
                    else:
                        evidence_data.append([f"--- TEXT FROM PAGE {page_num} ---"])
                        evidence_data.append([page.extract_text()[:500] + "..."])
                
    except Exception as e:
        print(f"Evidence generation failed: {e}")

    # Save CSV
    if evidence_data:
        csv_filename = f"{company_id}_verification_evidence.csv"
        csv_path = UPLOAD_DIR / csv_filename
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(evidence_data)
        
        VERIFICATION_SHEETS_DB[company_id] = str(csv_path)

async def process_filing(file_path: Path, company_id: str, filing_id: int, db: Session | None):
    text_pages = extract_text_from_pdf(file_path)
    chunks = chunk_text(text_pages)
    
    # 1. Extract
    metrics, full_text = await extract_financial_metrics(chunks, company_id, file_path.name)
    

    # 2. Verify
    await verify_extraction(metrics, full_text, company_id)
    if full_text:
        FULL_TEXT_DB[company_id] = full_text
    
    # 3. Generate Evidence
    if metrics:
        generate_evidence_csv(file_path, company_id, metrics)

    if db:
        pass
    return len(chunks)
