# backend/gateway.py
from __future__ import annotations
import os
import json
import time
import asyncio
from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass
import httpx
from pydantic import BaseModel, Field

# =============================================================================
# Configuration
# =============================================================================

@dataclass(frozen=True)
class GatewayConfig:
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    cloudinary_base_url: str = os.getenv("CLOUDINARY_BASE_URL", "https://api.cloudinary.com/v1_1")
    cloudinary_cloud_name: str = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    cloudinary_api_key: str = os.getenv("CLOUDINARY_API_KEY", "")
    cloudinary_api_secret: str = os.getenv("CLOUDINARY_API_SECRET", "")
    timeout_seconds: float = float(os.getenv("GATEWAY_TIMEOUT", "30"))
    retries: int = int(os.getenv("GATEWAY_RETRIES", "2"))
    retry_backoff_seconds: float = float(os.getenv("GATEWAY_RETRY_BACKOFF", "0.6"))
    circuit_fail_threshold: int = int(os.getenv("GATEWAY_CB_FAILS", "4"))
    circuit_cooldown_seconds: float = float(os.getenv("GATEWAY_CB_COOLDOWN", "10"))


# =============================================================================
# Data Transfer Objects (DTOs)
# =============================================================================

class GenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: bool = False
    options: Optional[Dict[str, Any]] = None

class GenerateResponse(BaseModel):
    response: str = Field(..., description="Model's full text response")

class EmbeddingsRequest(BaseModel):
    model: str
    input: List[str]

class EmbeddingsResponse(BaseModel):
    embeddings: List[List[float]]

class CloudinaryUploadResponse(BaseModel):
    public_id: str
    secure_url: str


# =============================================================================
# Exceptions
# =============================================================================

class GatewayError(RuntimeError):
    pass

class UpstreamTimeout(GatewayError):
    pass

class UpstreamUnavailable(GatewayError):
    pass

class BadUpstreamResponse(GatewayError):
    pass


# =============================================================================
# Minimal Circuit Breaker
# =============================================================================

class CircuitBreaker:
    def __init__(self, fail_threshold: int, cooldown_seconds: float) -> None:
        self.fail_threshold = fail_threshold
        self.cooldown_seconds = cooldown_seconds
        self._fail_count = 0
        self._open_until = 0.0
        self._lock = asyncio.Lock()

    async def allow(self) -> None:
        async with self._lock:
            now = time.monotonic()
            if self._open_until > now:
                raise UpstreamUnavailable(f"Circuit open until {self._open_until - now:.1f}s")
            if self._open_until and now >= self._open_until:
                self._fail_count = 0
                self._open_until = 0.0

    async def report_success(self) -> None:
        async with self._lock:
            self._fail_count = 0
            self._open_until = 0.0

    async def report_failure(self) -> None:
        async with self._lock:
            self._fail_count += 1
            if self._fail_count >= self.fail_threshold:
                self._open_until = time.monotonic() + self.cooldown_seconds


# =============================================================================
# Gateway
# =============================================================================

class Gateway:
    """
    Centralized handler for external service interactions.
    Currently supports: Ollama (generate/embeddings) and Cloudinary (optional).
    """

    def __init__(self, cfg: Optional[GatewayConfig] = None) -> None:
        self.cfg = cfg or GatewayConfig()
        self._client = httpx.AsyncClient(timeout=self.cfg.timeout_seconds)
        self._cb_ollama = CircuitBreaker(self.cfg.circuit_fail_threshold, self.cfg.circuit_cooldown_seconds)
        self._cb_cloudinary = CircuitBreaker(self.cfg.circuit_fail_threshold, self.cfg.circuit_cooldown_seconds)

    # -----------------------
    # Internal helper
    # -----------------------
    async def _request_with_retry(
        self,
        cb: CircuitBreaker,
        method: str,
        url: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth: Optional[Tuple[str, str]] = None,
        expected_status: int = 200,
    ) -> httpx.Response:
        await cb.allow()
        tries = self.cfg.retries + 1
        last_exc: Optional[Exception] = None

        for attempt in range(tries):
            try:
                resp = await self._client.request(
                    method, url, json=json_body, data=data, headers=headers, auth=auth
                )
                if resp.status_code == expected_status:
                    await cb.report_success()
                    return resp

                if resp.status_code in (408, 429, 500, 502, 503, 504):
                    last_exc = UpstreamUnavailable(f"Upstream {url} returned {resp.status_code}")
                    await asyncio.sleep(self.cfg.retry_backoff_seconds * (attempt + 1))
                    continue

                text = (resp.text or "")[:512]
                await cb.report_failure()
                raise BadUpstreamResponse(f"Bad status {resp.status_code} from {url}: {text}")

            except httpx.ReadTimeout:
                last_exc = UpstreamTimeout(f"Timeout calling {url}")
                await cb.report_failure()
                await asyncio.sleep(self.cfg.retry_backoff_seconds * (attempt + 1))
            except httpx.HTTPError as e:
                last_exc = UpstreamUnavailable(f"HTTP error calling {url}: {e}")
                await cb.report_failure()
                await asyncio.sleep(self.cfg.retry_backoff_seconds * (attempt + 1))

        raise last_exc or UpstreamUnavailable(f"Failed to call {url}")

    # -----------------------
    # Ollama
    # -----------------------

    async def ollama_generate(self, req: GenerateRequest) -> GenerateResponse:
        """Send a text generation request to Ollama."""
        url = f"{self.cfg.ollama_base_url}/api/generate"
        payload = req.model_dump()
        resp = await self._request_with_retry(self._cb_ollama, "POST", url, json_body=payload, expected_status=200)
        try:
            if req.stream:
                lines = [json.loads(line) for line in resp.text.strip().splitlines() if line.strip()]
                full = "".join([x.get("response", "") for x in lines])
                return GenerateResponse(response=full)
            else:
                data = resp.json()
                return GenerateResponse(response=data.get("response", ""))
        except Exception as e:
            raise BadUpstreamResponse(f"Failed parsing Ollama response: {e}")

    async def ollama_embeddings(self, req: EmbeddingsRequest) -> EmbeddingsResponse:
        """Send an embedding request to Ollama (supports multiple API versions)."""
        url = f"{self.cfg.ollama_base_url}/api/embeddings"
        payload = {"model": req.model}
        if isinstance(req.input, list):
            if len(req.input) == 1:
                payload["input"] = req.input[0]
                payload["prompt"] = req.input[0]
            else:
                payload["input"] = req.input
                payload["prompt"] = " \n".join(req.input)
        else:
            payload["input"] = req.input
            payload["prompt"] = req.input

        resp = await self._request_with_retry(self._cb_ollama, "POST", url, json_body=payload, expected_status=200)
        try:
            data = resp.json()

            if isinstance(data.get("embeddings"), list) and data["embeddings"]:
                return EmbeddingsResponse(embeddings=data["embeddings"])

            if isinstance(data.get("embedding"), list) and data["embedding"]:
                return EmbeddingsResponse(embeddings=[data["embedding"]])

            raise BadUpstreamResponse(f"Empty embeddings in response: {data}")
        except Exception as e:
            raise BadUpstreamResponse(f"Failed parsing Ollama embeddings: {e}")

    # -----------------------
    # Cloudinary (optional)
    # -----------------------

    async def cloudinary_upload_image(
        self,
        file_bytes: bytes,
        filename: str,
        folder: Optional[str] = None,
        resource_type: str = "image",
    ) -> CloudinaryUploadResponse:
        """
        Upload an image to Cloudinary.
        Uses basic authentication for demonstration; production setups should use signed uploads.
        """
        if not (self.cfg.cloudinary_cloud_name and self.cfg.cloudinary_api_key and self.cfg.cloudinary_api_secret):
            raise GatewayError("Cloudinary credentials missing")

        url = f"{self.cfg.cloudinary_base_url}/{self.cfg.cloudinary_cloud_name}/{resource_type}/upload"
        data = {
            "folder": folder or "",
            "public_id": os.path.splitext(filename)[0],
            "upload_preset": os.getenv("CLOUDINARY_UPLOAD_PRESET", ""),
        }


        files = {"file": (filename, file_bytes)}
        await self._cb_cloudinary.allow()
        try:
            async with httpx.AsyncClient(timeout=self.cfg.timeout_seconds) as c:
                resp = await c.post(url, data=data, files=files, auth=(self.cfg.cloudinary_api_key, self.cfg.cloudinary_api_secret))
            if resp.status_code == 200:
                await self._cb_cloudinary.report_success()
                body = resp.json()
                return CloudinaryUploadResponse(public_id=body["public_id"], secure_url=body["secure_url"])
            if resp.status_code in (408, 429, 500, 502, 503, 504):
                await self._cb_cloudinary.report_failure()
                raise UpstreamUnavailable(f"Cloudinary temp error {resp.status_code}")
            await self._cb_cloudinary.report_failure()
            raise BadUpstreamResponse(f"Cloudinary bad status {resp.status_code}: {resp.text[:256]}")
        except httpx.ReadTimeout:
            await self._cb_cloudinary.report_failure()
            raise UpstreamTimeout("Cloudinary timeout")
        except httpx.HTTPError as e:
            await self._cb_cloudinary.report_failure()
            raise UpstreamUnavailable(f"Cloudinary HTTP error: {e}")

    # -----------------------
    # Cleanup
    # -----------------------

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
