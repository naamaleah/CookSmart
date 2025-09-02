# backend/api/routers/ai_agent.py
from fastapi import APIRouter, Depends, Query

from backend.api.deps import get_gateway
from backend.gateway import Gateway
from backend.services.ai_agent_service import AIAgentService

# Router for AI Agent endpoints (no prefix for cleaner URLs)
router = APIRouter(prefix="", tags=["AI Agent"])

@router.get("/ask")
async def consult_ai(
    question: str = Query(..., min_length=3, description="Question for the AI Agent"),
    gateway: Gateway = Depends(get_gateway),
):
    """
    Send a one-time question to the LLM (without conversation history).
    Returns a short text-based answer.
    """
    svc = AIAgentService(gateway)
    answer = await svc.ask(question)
    return {"answer": answer}
