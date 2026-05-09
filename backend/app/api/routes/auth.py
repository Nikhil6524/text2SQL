from fastapi import APIRouter, HTTPException

from app.core.security import authenticate_credentials, session_manager
from app.models.schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    if not authenticate_credentials(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return LoginResponse(**session_manager.create_token(payload.username))
