import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    github_username: str
    oauth_token: str | None = None
    created_at: datetime


class Repository(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    github_repo_id: int
    owner: str = ""
    name: str
    description: str | None = None
    language_stats: dict | None = None
    stars: int = 0
    forks: int = 0
    last_commit_at: datetime | None = None
    is_stale: bool = False
    created_at: datetime


class GeneratedDocument(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    type: str
    content: str
    status: str = "draft"
    created_at: datetime


class Resume(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    raw_text: str
    file_path: str | None = None
    created_at: datetime


class JobDescription(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    raw_text: str
    source_url: str | None = None
    created_at: datetime


class SkillGapReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    job_description_id: uuid.UUID
    gaps: list | dict
    created_at: datetime


class LearningPlan(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    items: list | dict
    created_at: datetime


class InterviewSession(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    job_description_id: uuid.UUID
    questions: list | dict
    answers: dict
    created_at: datetime


class SocialPost(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    repository_id: uuid.UUID
    platform: str
    content: str
    status: str = "draft"
    created_at: datetime


class Notification(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    event_type: str
    channel: str
    sent_at: datetime | None = None
    status: str = "pending"
    created_at: datetime


class AnalyticsSnapshot(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    period: str
    metrics: dict
    created_at: datetime
