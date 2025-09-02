# backend/services/ai_agent_service.py
from __future__ import annotations

from typing import Optional
import os
from dotenv import load_dotenv

# Use Gateway instead of direct requests
from backend.gateway import Gateway, GenerateRequest

load_dotenv()

class AIAgentService:
    """
    Service for interacting with the LLM through a unified Gateway.
    """

    def __init__(self, gateway: Gateway):
        self.gateway = gateway
        self.model_name = os.getenv("OLLAMA_MODEL", "llama3")

    async def ask(self, question: str, *, system: Optional[str] = None) -> str:
        """
        Send a prompt to the LLM via the Gateway and return a textual response.
        """
        if not isinstance(question, str) or not question.strip():
            return "Question must be a non-empty string."

        prompt = f"{system}\n\n{question}" if system else question
        res = await self.gateway.ollama_generate(
            GenerateRequest(model=self.model_name, prompt=prompt, stream=False)
        )
        return (res.response or "").strip()
