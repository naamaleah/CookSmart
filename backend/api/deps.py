# backend/api/deps.py
from __future__ import annotations

from fastapi import Request

from backend.gateway import Gateway


def get_gateway(request: Request) -> Gateway:
    """
    Retrieve the Gateway instance stored in app.state.gateway.
    Allows using Depends(get_gateway) without creating circular imports.
    """
    gw = getattr(request.app.state, "gateway", None)
    if gw is None:
        raise RuntimeError("Gateway was not initialized on app.state.gateway")
    return gw
