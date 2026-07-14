from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.services import auth as auth_service
from app.core.config import settings
from app.core.security import decode_access_token
from app.infrastructure.database import get_db
from app.presentation.dependencies import get_current_user

logger = get_logger()
router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    pat: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/login")
async def login_with_pat(body: LoginRequest, session: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        result = await auth_service.authenticate_with_pat(session, body.pat)
        return TokenResponse(**result)
    except Exception as exc:
        logger.error("login failed", exc_info=exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PAT or GitHub API error")


@router.get("/oauth-url")
async def oauth_url() -> dict:
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="GitHub OAuth not configured")
    return {"url": auth_service.get_oauth_url()}


@router.get("/callback")
async def oauth_callback(code: str, session: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        result = await auth_service.handle_oauth_callback(session, code)
        return TokenResponse(**result)
    except Exception as exc:
        logger.error("oauth callback failed", exc_info=exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OAuth handshake failed")


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)) -> dict:
    return user
