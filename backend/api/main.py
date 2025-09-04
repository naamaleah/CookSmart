# backend/api/main.py
from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

# Load environment variables from .env file (optional but recommended)
load_dotenv()

from backend.api.routers import recipes, favorites, auth, ai_agent, rag, images

# Gateway dependency injection
from backend.gateway import Gateway, GatewayConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize a single Gateway instance for the entire application.
    Configuration parameters are loaded from environment variables via GatewayConfig.
    """
    app.state.gateway = Gateway(GatewayConfig())
    try:
        yield
    finally:
        await app.state.gateway.aclose()


# Create FastAPI app with lifespan management
app = FastAPI(lifespan=lifespan)

# Register routers
app.include_router(recipes.router)
app.include_router(favorites.router)
app.include_router(auth.router)
app.include_router(ai_agent.router)
app.include_router(rag.router)
app.include_router(images.router)
