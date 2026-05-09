from fastapi import Header

from app.core.security import validate_bearer_header


def get_current_user(authorization: str = Header(default="")) -> str:
    return validate_bearer_header(authorization)
