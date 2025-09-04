# backend/api/routers/recipes.py
from fastapi import APIRouter
from backend.services import recipes_command_service, recipes_query_service
from backend.services.recipes_command_service import NewRecipe

router = APIRouter(prefix="/recipes", tags=["Recipes"])

@router.post("/add")
def add_recipe(recipe: NewRecipe):
    """
    Add a new recipe to the system.
    Expects JSON with ingredients as a List[str].
    """
    return recipes_command_service.add_recipe(recipe)

@router.get("/search")
def search_recipes(name: str = None, category: str = None, area: str = None):
    return recipes_query_service.search_recipes(name, category, area)

@router.get("/search/by-ingredients")
def search_by_ingredients(ingredients: list[str]):
    return recipes_query_service.search_by_ingredients(ingredients)

@router.get("/{recipeid}")
def get_recipe_details(recipeid: int):
    return recipes_query_service.get_recipe_details(recipeid)

@router.get("/recommendations/{userid}")
def recommend_recipes(userid: int):
    return recipes_query_service.recommend_recipes(userid)
