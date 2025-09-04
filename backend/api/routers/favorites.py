# backend/api/routers/favorites.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.utils.auth_utils import get_current_user
from backend.services import favorites_command_service, favorites_query_service

# Router for managing user favorites
router = APIRouter(prefix="/favorites", tags=["Favorites"])

class FavoriteRequest(BaseModel):
    recipeid: int

@router.post("/")
def add_favorite(fav: FavoriteRequest, current_user: str = Depends(get_current_user)):
    """
    Add a recipe to the current user's list of favorites.
    """
    return favorites_command_service.add_favorite(fav.recipeid, current_user)

@router.get("/my")
def get_user_favorites(current_user: str = Depends(get_current_user)):
    """
    Retrieve all favorite recipes for the current user.
    """
    return favorites_query_service.get_user_favorites(current_user)

@router.delete("/{recipeid}")
def remove_favorite(recipeid: int, current_user: str = Depends(get_current_user)):
    """
    Remove a recipe from the current user's list of favorites.
    """
    return favorites_command_service.remove_favorite(recipeid, current_user)
