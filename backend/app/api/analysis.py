
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.services.orchestrator import orchestrate_analysis
from app.services.ingestion import FULL_TEXT_DB

router = APIRouter()

class AnalysisRequest(BaseModel):
    company_id: str
    question: str

@router.post("/analyze")
async def analyze_company(request: AnalysisRequest):
    print(f"Analyzing for: {request.company_id}")
    print(f"Available keys in DB: {list(FULL_TEXT_DB.keys())}")
    
    # 1. Retrieve Context
    context = FULL_TEXT_DB.get(request.company_id)
    
    if not context:
        print("Context not found in DB")
        # Fallback if no upload yet
        context = "The user has not uploaded an annual report yet. Answer generally or ask them to upload."
    else:
        print(f"Context found. Length: {len(context)}")

    try:
        # The orchestrator is designed to take (company_id, context) usually
        # But here we treat the 'question' as the trigger for a specific answer?
        # WAIT: The User wants a CHATBOT. 
        # orchestrate_analysis in this project was for the "Deep Dive Report".
        # We need a simple Q&A function.
        
        # Let's improvise a simple Q&A agent here using available tools
        from app.services.gemini import generate_content
        

        # Prepare prompt
        prompt = f"""
        You are a sophisticated Financial Analyst AI named "Analysis Assistant". 
        You are speaking to a professional investor or stakeholder.

        **CORE PERSONA & TONE:**
        - **Professional & Respectful**: Maintain a polite, objective, and high-level professional tone at all times.
        - **Insightful & Rational**: Do NOT just list data. Explain the *rationale* behind the numbers. Why did revenue grow? What drove the margin expansion? Connect the dots.
        - **Detailed**: Provide depth. The user wants to understand the *story* behind the financials.

        **CRITICAL SAFETY GUARDRAILS (MUST FOLLOW):**
        1.  **NO INVESTMENT ADVICE**: You function as an analyst, not a financial advisor. Do not recommend buying, selling, or holding stock. If asked for advice, politely demur and focus on the *fundamental analysis* of the data.
        2.  **NO HALLUCINATIONS**: Your knowledge is STRICTLY limited to the "ANNUAL REPORT CONTEXT" provided below.
            - If the user asks for a specific data point (e.g., "What was the Q4 attrition rate?") and it is **NOT** present in the text, you MUST clearly state: *"This specific data point is not available in the provided annual report documents."*
            - Do NOT make up numbers or guess.

        **STRUCTURE OF RESPONSE:**
        1.  **Direct Answer**: Address the user's specific question immediately.
        2.  **Strategic Rationale**: Explain the *why* and *how*. (e.g., "This increase was primarily driven by...")
        3.  **Supporting Data**: specific tables or bullet points with numbers from the text.
        4.  **📚 Detailed Sources**: THIS IS CRITICAL. You MUST list the exact location of the data.
            - Format: `**Source**: [Section Name] (Page [X])`
            - Example: `**Source**: Management Discussion & Analysis (Page 45); Consolidated Financial Statements (Page 112)`
            - If page number is not explicitly marked in text chunk, cite the Section Header.

        USER QUESTION: {request.question}

        --------------
        ANNUAL REPORT CONTEXT:
        {context[:500000]} 
        --------------

        ANSWER:
        """
        # 1. Generate Draft Analysis
        print(f"Generating draft analysis for question: {request.question}")
        draft_response = await generate_content(prompt)
        print("Draft analysis generated.")
        
        # 2. Quality Control & Formatting (The Reviewer Agent)
        try:
            print("Starting Quality Control (Reviewer Agent)...")
            review_prompt = f"""
            You are a Senior Editor and Quality Control Specialist.
            Your task is to polish the "DRAFT ANSWER" provided by a junior analyst.

            **QUALITY CHECKLIST:**
            1.  **Formatting**: Ensure standard Markdown. Use bolding for key terms. Ensure *generous* double spacing between paragraphs for readability.
            2.  **Artifact Removal**: The OCR often misreads the Indian Rupee symbol (₹) as "D". 
                - IF you see "D" followed by a number (e.g., "D1,346"), REPLACE "D" with "₹". (e.g., "₹1,346").
                - Fix any other obvious OCR artifacts.
            3.  **Detailed Sources**: Check if the "Detailed Sources" section exists at the bottom.
                - If it's missing, trying to infer it from the context if possible, or format the existing citations to look professional.
                - Ensure it looks like: `**Source**: [Section] (Page X)`
            4.  **Structure**: Ensure the answer has the 4 required sections: Direct Answer, Rationale, Supporting Data, Detailed Sources.
            5.  **Fact Check**: Do not change the specific numbers (unless fixing the currency symbol), but ensure the text explains them clearly.

            USER QUESTION: {request.question}

            DRAFT ANSWER:
            {draft_response}

            FINAL POLISHED OUTPUT:
            """
            
            final_response = await generate_content(review_prompt)
            print("Reviewer Agent finished.")
            return {"analysis": final_response}
            
        except Exception as review_error:
            print(f"Reviewer Agent failed: {str(review_error)}. Returning draft response.")
            # Fallback to draft if verification fails (latency/error)
            # Append a small note so we know it wasn't reviewed
            fallback = draft_response + "\n\n*(Note: Automated quality check skipped due to processing timeout)*"
            return {"analysis": fallback}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
