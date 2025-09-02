# backend/api/routers/auth.py
from fastapi import APIRouter, Body, Depends
from fastapi.security import OAuth2PasswordRequestForm
from backend.services import auth_command_service

# Router for authentication endpoints
router = APIRouter(tags=["Authentication"])

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate a user using username and password.
    Returns an access token if successful.
    """
    return auth_command_service.login_user(form_data.username, form_data.password)

@router.post("/register")
def register(
    username: str = Body(..., description="Desired username"),
    password: str = Body(..., description="User password"),
    email: str = Body(..., description="User email address"),
    phone: str = Body(..., description="User phone number"),
):
    """
    Register a new user with username, password, email, and phone.
    Returns confirmation details of the newly created user.
    """
    return auth_command_service.register_user(username, password, email, phone)
