from pydantic import BaseModel, Field
from typing import List, Optional, Any
import openai
import os
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.crud.b2b_saas_context import (
    create_b2b_saas_context,
    get_b2b_saas_context_by_id,
    get_all_b2b_saas_context,
    search_similar_b2b_saas_context,
    search_similar_b2b_saas_context_by_text
)
from dotenv import load_dotenv

load_dotenv(".env")
router = APIRouter(prefix="/b2b_saas_context", tags=["b2b_saas_context"])

# ---------------------- Pydantic Models ----------------------

class LLMAnswerRequest(BaseModel):
    ticket_id: str
    description: str
    feature: Optional[str] = None
    top_k: int = 5

class LLMAnswerResponse(BaseModel):
    llm_answer: Any  # Can hold parsed JSON or error dictionary
    used_context: list

class B2BSaasContextBase(BaseModel):
    url: str
    title: Optional[str] = None
    chunk_order: int = 0
    embedding: List[float]
    chunk_metadata: Optional[Any] = None

class B2BSaasContextCreate(B2BSaasContextBase):
    pass

class B2BSaasContextOut(B2BSaasContextBase):
    id: int
    created_at: Any
    class Config:
        from_attributes = True

class B2BSaasContextWithSimilarity(BaseModel):
    record: B2BSaasContextOut
    similarity: float

# ---------------------- Helper Functions ----------------------

def build_llm_prompt(ticket_id: str, description: str, feature: Optional[str], retrieved: list) -> str:
    context_chunks = []
    for item in retrieved[:2]:
        rec = item['record']
        chunk_text = rec.chunk_metadata.get('chunk_text', '') if rec.chunk_metadata else ''
        context_chunks.append(
            f"Title: {rec.title}\nContent: {chunk_text}\nSimilarity: {item['similarity']:.3f}"
        )
    context_str = '\n---\n'.join(context_chunks)

    prompt = f"""
You are an AI Product Analyst. Your job is to transform raw customer support tickets into:
1. Actionable hypotheses
2. A/B test variant ideas

Return ONLY valid JSON. Do not include explanations, markdown, or extra text.

### Input Ticket
TicketId: {ticket_id}
Feature: {feature}
Description: {description}

### Context
{context_str}

### Instructions
For Rank1 and Rank2, output a single statement in this format:
"If we [change], then [KPI] will improve because users say [pain point]."

Example:
Statement: "If we launch an in-app, step-by-step setup wizard with progress bar and checklist, then first-time-setup completion will improve because users say 'Please assist.'"

Generate a JSON object with the following format:

{{
  "TicketId": "{ticket_id}",
  "SuggestedHypotheses": {{
    "Rank1": {{
      "hypothesis": "<hypothesis in required format with source reference>",
      "ABVariantIdeas": [
        "<variant idea 1 with source reference>",
        "<variant idea 2 with source reference>"
      ]
    }},
    "Rank2": {{
      "hypothesis": "<hypothesis in required format with source reference>",
      "ABVariantIdeas": [
        "<variant idea 1 with source reference>",
        "<variant idea 2 with source reference>"
      ]
    }}
  }},
  "ExactPhrasesEvidence": {{
    "FromTicket": "<quote or paraphrased ticket evidence>",
    "FromResearch": "<title + link>"
  }}
}}

Respond with ONLY the JSON object.
"""
    return prompt


def try_parse_json(text: str):
    """Attempt JSON parsing after cleaning common artifacts."""
    text_clean = text.strip().lstrip("```json").rstrip("```").strip()
    return json.loads(text_clean)

# ---------------------- Routes ----------------------

@router.post("/answer_with_llm", response_model=LLMAnswerResponse)
async def answer_with_llm(request: LLMAnswerRequest):
    # Retrieve similar context
    retrieved = await search_similar_b2b_saas_context_by_text(request.description, request.top_k)

    # Build prompt
    prompt = build_llm_prompt(
        request.ticket_id,
        request.description,
        request.feature,
        retrieved
    )

    # Use OpenAI API
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return LLMAnswerResponse(
            llm_answer={"error": "OPENAI_API_KEY not set in environment."},
            used_context=[]
        )
    client = openai.OpenAI(api_key=openai_api_key)
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.2,
        )
        raw_answer = response.choices[0].message.content.strip()
        try:
            llm_answer_parsed = try_parse_json(raw_answer)
        except json.JSONDecodeError:
            llm_answer_parsed = {
                "error": "Invalid JSON format returned by OpenAI",
                "raw_output": raw_answer
            }
    except Exception as e:
        llm_answer_parsed = {"error": str(e)}

    return LLMAnswerResponse(
        llm_answer=llm_answer_parsed,
        used_context=[
            {
                "title": r['record'].title,
                "chunk_text": r['record'].chunk_metadata.get('chunk_text', '') if r['record'].chunk_metadata else '',
                "similarity": r['similarity']
            } for r in retrieved
        ]
    )

@router.post("/", response_model=B2BSaasContextOut)
async def create_context(context: B2BSaasContextCreate, db: AsyncSession = Depends(get_db)):
    data = context.dict()
    obj = await create_b2b_saas_context(data)
    return obj

@router.get("/{context_id}", response_model=B2BSaasContextOut)
async def get_context(context_id: int, db: AsyncSession = Depends(get_db)):
    obj = await get_b2b_saas_context_by_id(context_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Not found")
    return obj

@router.get("/", response_model=List[B2BSaasContextOut])
async def get_all_contexts(db: AsyncSession = Depends(get_db)):
    return await get_all_b2b_saas_context()

class TicketTextQuery(BaseModel):
    ticket_text: str
    top_k: int = 5

@router.post("/search_similar", response_model=List[B2BSaasContextWithSimilarity])
async def search_similar_contexts_by_text(query: TicketTextQuery):
    results = await search_similar_b2b_saas_context_by_text(query.ticket_text, query.top_k)
    return [
        B2BSaasContextWithSimilarity(
            record=B2BSaasContextOut.from_orm(r['record']),
            similarity=r['similarity']
        )
        for r in results
    ]
