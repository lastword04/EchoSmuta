from fastapi import Response
from ....settings import settings


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        expires=settings.user_access_token.expire_minutes * 60,  # Convert minutes to seconds
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        expires=settings.refresh_token.expire_minutes * 60,
        path="/"
    )