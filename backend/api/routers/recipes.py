# backend/api/routers/recipes.py
from fastapi import APIRouter, Query
from typing import List
from backend.services import recipes_command_service, recipes_query_service
from backend.services.recipes_command_service import NewRecipe

# Router for recipe management and queries
router = APIRouter(prefix="", tags=["Recipes"])

@router.post("/add")
def add_recipe(recipe: NewRecipe):
    """
    Add a new recipe to the system.
    """
    return recipes_command_service.add_recipe(recipe)


@router.get("/search")
def search_recipes(name: str = Query(None, description="Recipe name"),
                   category: str = Query(None, description="Recipe category"),
                   area: str = Query(None, description="Recipe area/cuisine")):
    """
    Search recipes by optional filters such as name, category, or area.
    """
    return recipes_query_service.search_recipes(name, category, area)


@router.get("/search/by-ingredients")
def search_by_ingredients(ingredients: List[str] = Query(..., description="List of ingredients")):
    """
    Search recipes based on a list of ingredients.
    """
    return recipes_query_service.search_by_ingredients(ingredients)


@router.get("/{recipeid}")
def get_recipe_details(recipeid: int):
    """
    Retrieve detailed information about a specific recipe by its ID.
    """
    return recipes_query_service.get_recipe_details(recipeid)


@router.get("/recommendations/{userid}")
def recommend_recipes(userid: int):
    """
    Retrieve personalized recipe recommendations for a given user.
    """
    return recipes_query_service.recommend_recipes(userid)
