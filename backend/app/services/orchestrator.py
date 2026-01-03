
import json
import re
from app.services.gemini import generate_content, MODEL_PRO
from app.core.prompts import (
    ANALYSIS_SYSTEM_PROMPT, REVIEW_SYSTEM_PROMPT, 
    CONTRADICTION_SYSTEM_PROMPT, GAP_SYSTEM_PROMPT, FINAL_SYSTEM_PROMPT
)

def parse_json(text: str):
    """Clean and parse JSON from LLM output."""
    try:
        # Remove markdown code blocks if present
        cleaned_text = re.sub(r"```json\s*", "", text)
        cleaned_text = re.sub(r"```", "", cleaned_text)
        return json.loads(cleaned_text.strip())
    except Exception as e:
        print(f"Error parsing JSON: {e}. Text: {text[:100]}...")
        return {}

async def run_analysis_agent(context_text: str):
    prompt = f"{ANALYSIS_SYSTEM_PROMPT}\n\n[CONTEXT]\n{context_text}"
    return await generate_content(prompt)

async def run_review_agent(context_text: str, draft_analysis: str):
    prompt = f"{REVIEW_SYSTEM_PROMPT}\n\n[CONTEXT]\n{context_text}\n\n[DRAFT_ANALYSIS]\n{draft_analysis}"
    response_text = await generate_content(prompt)
    
    # Heuristic: The agent is asked to output REVISED_ANALYSIS, QUALITY_SCORES (json), COMMENTS.
    # It might not be pure JSON. We might need to split.
    # For now, let's assume the prompt instructions lead to a structured text response we can parse.
    # Or better, let's refine the review agent to just output a JSON object or specific separators.
    # Given the prompt asks for "Output: 1... 2... 3...", I'll try to extract them via regex or just return text for now.
    # To make it robust as an API, let's just return the full text for step 1 of v1, 
    # but the orchestrator needs the scores.
    # Let's try to extract JSON block for scores.
    
    scores = {}
    try:
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if json_match:
            scores = json.loads(json_match.group(0))
    except:
        pass
        
    return response_text, scores

async def run_contradiction_agent(context_text: str, reviewed_analysis: str):
    prompt = f"{CONTRADICTION_SYSTEM_PROMPT}\n\n[CONTEXT]\n{context_text}\n\n[REVIEWED_ANALYSIS]\n{reviewed_analysis}"
    response_text = await generate_content(prompt)
    return parse_json(response_text)

async def run_gap_agent(context_text: str, reviewed_analysis: str):
    prompt = f"{GAP_SYSTEM_PROMPT}\n\n[CONTEXT]\n{context_text}\n\n[REVIEWED_ANALYSIS]\n{reviewed_analysis}"
    response_text = await generate_content(prompt)
    return parse_json(response_text)

async def run_final_agent(context_text: str, reviewed_analysis: str, quality_scores: dict, contradiction_report: dict, gap_report: dict):
    payload = {
        "reviewed_analysis": reviewed_analysis,
        "quality_scores": quality_scores,
        "contradiction_report": contradiction_report,
        "gap_report": gap_report,
    }
    prompt = f"{FINAL_SYSTEM_PROMPT}\n\n[CONTEXT]\n{context_text}\n\n[AGENT_INPUT]\n{json.dumps(payload, default=str)}"
    response_text = await generate_content(prompt)
    return parse_json(response_text)

async def orchestrate_analysis(company_name: str, context_data: str):
    # 1. Analysis
    draft = await run_analysis_agent(context_data)
    
    # 2. Review
    reviewed_text, scores = await run_review_agent(context_data, draft)
    # If regex failed to separate, reviewed_text is the whole thing. 
    # We'll treat the whole output of review as the "reviewed analysis" for the next steps 
    # (though ideally we strip comments).
    
    # 3. Contradiction
    contradictions = await run_contradiction_agent(context_data, reviewed_text)
    
    # 4. Gaps
    gaps = await run_gap_agent(context_data, reviewed_text)
    
    # 5. Final
    final_result = await run_final_agent(context_data, reviewed_text, scores, contradictions, gaps)
    
    return final_result
