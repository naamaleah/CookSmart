# backend/services/embedding_service.py
from typing import List

from backend.gateway import Gateway, UpstreamUnavailable, EmbeddingsRequest


class EmbeddingUnavailable(Exception):
    """Raised when embeddings are unavailable/unsupported or if upstream fails repeatedly."""
    pass


class EmbeddingService:
    """
    Service wrapper for asynchronous embedding calls through the Gateway.
    """

    def __init__(self, gateway: Gateway, model: str = "nomic-embed-text"):
        self.gateway = gateway
        self.model = model  # Recommended to configure via environment variables

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        Returns a list of embedding vectors.
        """
        if not texts:
            return []
        try:
            res = await self.gateway.ollama_embeddings(
                EmbeddingsRequest(model=self.model, input=texts)
            )
            return res.embeddings
        except UpstreamUnavailable as e:
            raise EmbeddingUnavailable(str(e)) from e

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text.
        Returns one embedding vector.
        """
        if not isinstance(text, str) or not text.strip():
            return []
        vectors = await self.embed_texts([text])
        return vectors[0] if vectors else []
