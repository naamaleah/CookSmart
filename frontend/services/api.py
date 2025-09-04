# frontend/services/api.py
import requests
import random
from config import API_BASE_URL
from typing import Any, Dict, Tuple, Optional
import random
# ===== Local Ollama (used for quick AI tips) =====
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"
OLLAMA_TIMEOUT = (8, 120)

# ---------------------------
# Internal helper
# ---------------------------
def _request(method: str, path: str,
             token: Optional[str] = None,
             **kwargs) -> Dict[str, Any]:
    """
    Internal helper for HTTP API requests.
    - Automatically attaches Authorization header if a token is provided.
    - Raises for non-2xx responses.
    - Returns parsed JSON.
    """
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"

    r = requests.request(method, f"{API_BASE_URL}{path}", headers=headers, **kwargs)
    r.raise_for_status()
    return r.json()


# ---------------------------
# Authentication & Users
# ---------------------------
def login_user(username: str, password: str) -> Tuple[bool, str]:
    """Attempt login. Returns (success, token/message)."""
    try:
        resp = _request("POST", "/auth/login",
                        data={"username": username, "password": password},
                        timeout=30)
        return True, resp.get("access_token", "")
    except requests.RequestException as e:
        try:
            return False, e.response.json().get("detail", "Invalid username or password.")
        except Exception:
            return False, str(e)


def register_user(username: str, password: str, email: str, phone: str) -> Tuple[bool, str]:
    """Attempt user registration. Returns (success, message)."""
    try:
        _request("POST", "/auth/register",
                 json={"username": username, "password": password,
                       "email": email, "phone": phone},
                 timeout=30)
        return True, "Registered successfully."
    except requests.RequestException as e:
        try:
            return False, e.response.json().get("detail", "Registration failed.")
        except Exception:
            return False, str(e)


# ---------------------------
# Favorites
# ---------------------------
def add_to_favorites(token: str, recipe_id: int) -> Tuple[bool, str]:
    """Add a recipe to the user's favorites."""
    try:
        _request("POST", "/favorites/",
                 token=token, json={"recipeid": recipe_id}, timeout=30)
        return True, "Added to favorites."
    except requests.RequestException as e:
        try:
            return False, e.response.json().get("detail", "Failed to add.")
        except Exception:
            return False, str(e)


def get_favorites(token: str):
    """Fetch all favorite recipes for the current user."""
    try:
        return _request("GET", "/favorites/my", token=token, timeout=30)
    except Exception:
        return []


def remove_from_favorites(token: str, recipe_id: int) -> Tuple[bool, str]:
    """Remove a recipe from the user's favorites."""
    try:
        _request("DELETE", f"/favorites/{recipe_id}", token=token, timeout=30)
        return True, "Removed from favorites."
    except requests.RequestException as e:
        try:
            return False, e.response.json().get("detail", "Failed to remove.")
        except Exception:
            return False, str(e)


# ---------------------------
# Recipes
# ---------------------------
def search_recipes(query: str):
    """Search for recipes by name."""
    try:
        return _request("GET", "/recipes/search",
                        params={"name": query}, timeout=30)
    except Exception:
        return []


def search_by_ingredients(ingredients_list):
    """Search for recipes that contain one or more of the given ingredients."""
    try:
        params = [("ingredients", ing) for ing in ingredients_list]
        return _request("GET", "/recipes/search/by-ingredients",
                        params=params, timeout=45)
    except Exception:
        return []



def upload_image(token: str, image_path: str) -> tuple[bool, str]:
    """Upload an image file to Cloudinary via backend."""
    url = f"{API_BASE_URL}/images/upload"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        with open(image_path, "rb") as f:
            files = {"image": f}
            r = requests.post(url, headers=headers, files=files, timeout=60)
            r.raise_for_status()
            return True, r.json().get("secure_url", "")
    except requests.RequestException as e:
        return False, str(e)


def add_recipe(token: str, name: str, category: str,
               area: str, instructions: str,
               thumbnail_url: str, ingredients: list[str]):
    """Add a new recipe with JSON"""
    url = f"{API_BASE_URL}/recipes/add"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": name,
        "category": category,
        "area": area,
        "instructions": instructions,
        "thumbnail_url": thumbnail_url,
        "ingredients": ingredients,
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return True, "Recipe added."
    except requests.RequestException as e:
        return False, str(e)


def get_recommendations(userid: int):
    """Get recommended recipes for a specific user."""
    try:
        return _request("GET", f"/recipes/recommendations/{userid}", timeout=30)
    except Exception:
        return []


# ---------------------------
# Quick AI tip (via local Ollama)
# ---------------------------
def ask_ai_agent(question: str) -> str:
    """
    Ask the local Ollama model for a short AI-generated tip.
    Returns a string response or an error message.
    """
    seed = random.randint(1, 1_000_000)
    payload = {
        "model": MODEL_NAME,
        "prompt": question,
        "stream": False,
        "options": {"temperature": 0.9, "top_p": 1.0, "seed": seed},
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        r.raise_for_status()
        return (r.json().get("response") or "").strip() or "No tip available."
    except Exception as e:
        return f"AI tip error: {e}"


# ---------------------------
# RAG endpoints
# ---------------------------
def rag_chat(message: str, session_id: str | None, token: str, timeout_sec: int = 240) -> dict:
    """Send a chat message to the RAG backend and return the response."""
    return _request("POST", "/rag/chat", token=token,
                    json={"message": message, "session_id": session_id},
                    timeout=timeout_sec)


def rag_ingest(title: str, source: str, full_text: str, token: str) -> dict:
    """Ingest a new document into the RAG knowledge base."""
    return _request("POST", "/rag/ingest", token=token,
                    params={"title": title, "source": source},
                    json=full_text, timeout=120)


def rag_get_history(session_id: str, token: str, limit: int = 200) -> dict:
    """Retrieve chat history for a specific session."""
    return _request("GET", "/rag/history", token=token,
                    params={"session_id": session_id, "limit": limit}, timeout=60)


def rag_get_or_create_session(token: str) -> dict:
    """Get the latest RAG session ID or create a new one."""
    return _request("GET", "/rag/session/get-or-create", token=token, timeout=30)


def rag_delete_session(session_id: str, token: str) -> dict:
    """Delete a specific RAG session and its messages."""
    return _request("DELETE", f"/rag/session/{session_id}", token=token, timeout=60)


def rag_delete_latest_session(token: str) -> dict:
    """Delete the most recent RAG session for the current user (if any)."""
    return _request("DELETE", "/rag/session/current", token=token, timeout=60)
