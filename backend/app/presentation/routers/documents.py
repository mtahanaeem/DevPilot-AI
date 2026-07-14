from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.application.services import document as doc_service
from app.infrastructure.database import get_db
from app.presentation.dependencies import get_current_user

logger = get_logger()
router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentOut(BaseModel):
    id: str
    repository_id: str
    type: str
    content: str
    status: str
    created_at: str


class GenerateRequest(BaseModel):
    repo_id: str


class RegenerateRequest(BaseModel):
    feedback: str


@router.post("/generate")
async def generate_document(
    body: GenerateRequest,
    doc_type: str = Query("readme", pattern="^(readme|contributing|architecture)$"),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentOut:
    doc = await doc_service.generate_document(session, user["id"], body.repo_id, user.get("pat", ""), doc_type)
    return DocumentOut(
        id=str(doc.id),
        repository_id=str(doc.repository_id),
        type=doc.type,
        content=doc.content,
        status=doc.status,
        created_at=doc.created_at.isoformat(),
    )


@router.get("")
async def list_documents(
    repo_id: str | None = Query(None),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[DocumentOut]:
    docs = await doc_service.list_drafts(session, user["id"], repo_id)
    return [
        DocumentOut(
            id=str(d.id),
            repository_id=str(d.repository_id),
            type=d.type,
            content=d.content,
            status=d.status,
            created_at=d.created_at.isoformat(),
        )
        for d in docs
    ]


@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentOut:
    doc = await doc_service.get_document(session, doc_id, user["id"])
    return DocumentOut(
        id=str(doc.id),
        repository_id=str(doc.repository_id),
        type=doc.type,
        content=doc.content,
        status=doc.status,
        created_at=doc.created_at.isoformat(),
    )


@router.post("/{doc_id}/approve")
async def approve_document(
    doc_id: str,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentOut:
    try:
        doc = await doc_service.approve_document(session, doc_id, user["id"], user.get("pat", ""))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return DocumentOut(
        id=str(doc.id),
        repository_id=str(doc.repository_id),
        type=doc.type,
        content=doc.content,
        status=doc.status,
        created_at=doc.created_at.isoformat(),
    )


@router.post("/{doc_id}/regenerate")
async def regenerate_document(
    doc_id: str,
    body: RegenerateRequest,
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DocumentOut:
    doc = await doc_service.regenerate_document(session, doc_id, user["id"], body.feedback)
    return DocumentOut(
        id=str(doc.id),
        repository_id=str(doc.repository_id),
        type=doc.type,
        content=doc.content,
        status=doc.status,
        created_at=doc.created_at.isoformat(),
    )
