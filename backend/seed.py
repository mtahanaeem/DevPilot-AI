import asyncio
import uuid

from sqlalchemy import select
from structlog import get_logger

from app.core.config import settings
from app.infrastructure.database.session import async_session_factory, init_db
from app.infrastructure.database.models.user import UserModel
from app.infrastructure.database.models.repository import RepositoryModel
from app.infrastructure.database.models.document import GeneratedDocumentModel
from app.infrastructure.database.models.resume import ResumeModel

logger = get_logger()


async def seed() -> None:
    logger.info("Seeding database...")
    await init_db()

    async with async_session_factory() as session:
        result = await session.execute(select(UserModel).limit(1))
        existing = result.scalar_one_or_none()
        if existing:
            logger.info("Database already seeded, skipping")
            return

        user = UserModel(
            id=uuid.uuid4(),
            github_username="devpilot-user",
            oauth_token="placeholder-token",
        )
        session.add(user)
        await session.flush()

        repo = RepositoryModel(
            id=uuid.uuid4(),
            user_id=user.id,
            github_repo_id=123456789,
            name="sample-repo",
            description="A sample repository for development",
            language_stats={"Python": 60, "TypeScript": 30, "Shell": 10},
            stars=42,
            forks=7,
            last_commit_at=None,
            is_stale=False,
        )
        session.add(repo)
        await session.flush()

        doc = GeneratedDocumentModel(
            id=uuid.uuid4(),
            repository_id=repo.id,
            type="readme",
            content="# Sample Repo\n\nThis is an auto-generated README.",
            status="draft",
        )
        session.add(doc)

        resume = ResumeModel(
            id=uuid.uuid4(),
            user_id=user.id,
            raw_text="Sample developer resume with Python, TypeScript, and AI experience.",
            file_path="/data/resume.pdf",
        )
        session.add(resume)

        await session.commit()
        logger.info("Seed complete: 1 user, 1 repo, 1 doc, 1 resume created")


if __name__ == "__main__":
    asyncio.run(seed())
