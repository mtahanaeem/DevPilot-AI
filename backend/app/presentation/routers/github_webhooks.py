from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.services.github_webhooks import process_webhook, verify_signature
from app.infrastructure.database import get_db

logger = get_logger()
router = APIRouter(prefix="/github", tags=["github"])


@router.post("/webhook")
async def github_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> dict:
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    event = request.headers.get("X-GitHub-Event", "")

    if not verify_signature(body, signature):
        logger.warning("webhook signature verification failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    payload = await request.json()
    logger.info("webhook received", event=event)

    await process_webhook(session, event, payload)

    return {"status": "ok"}
