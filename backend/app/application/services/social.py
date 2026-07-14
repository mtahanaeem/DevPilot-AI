from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.exceptions import NotFoundError
from app.infrastructure.database.models.repository import RepositoryModel
from app.infrastructure.database.models.social import SocialPostModel
from app.infrastructure.github import GitHubClient
from app.infrastructure.llm import get_llm_provider

logger = get_logger()

PLATFORM_LIMITS = {
    "linkedin": 3000,
    "twitter": 280,
    "x": 280,
}


async def generate_post(
    session: AsyncSession, user_id: Any, repo_id: Any, platform: str, tone: str, pat: str
) -> SocialPostModel:
    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.id == repo_id, RepositoryModel.user_id == user_id)
    )
    repo = result.scalar_one_or_none()
    if repo is None:
        raise NotFoundError(f"Repository {repo_id} not found")

    client = GitHubClient(token=pat)
    try:
        try:
            readme = await client.get_file_content(repo.owner, repo.name, "README.md")
        except Exception:
            readme = ""
    finally:
        await client.close()

    max_chars = PLATFORM_LIMITS.get(platform, 3000)
    llm = get_llm_provider()

    repo_url = f"https://github.com/{repo.owner}/{repo.name}"

    prompt = f"""Repository: {repo.name}
URL: {repo_url}
Description: {repo.description or ''}
Stars: {repo.stars} | Forks: {repo.forks}
Language: {repo.language_stats or '(multiple)'}

README excerpt:
{readme[:2000] if readme else '(none)'}

Generate a high-end, engaging social media post announcing this repository with a {tone} tone for {platform}.
Requirements:
- Use emojis sparingly — only where they add meaning (e.g. 🚀 for launch, ⭐ for stars), not every line
- 3-5 relevant hashtags at the end on their own line
- A compelling hook at the start
- The repo URL ({repo_url}) naturally worked into the caption
- Proper formatting with line breaks between paragraphs for readability
- Maximum length: {max_chars} characters.

Make it sound premium and polished, like a tech influencer or startup founder announcing a launch."""

    content = await llm.generate(
        prompt,
        system=f"You are a top-tier social media manager for tech creators. Write a {tone} post for {platform} to announce a new open-source project. Use emojis sparingly (only where meaningful), include hashtags and a compelling hook. Max {max_chars} chars.",
        max_tokens=1024,
        temperature=0.8,
    )

    post = SocialPostModel(
        repository_id=repo.id,
        platform=platform,
        content=content.strip(),
        status="draft",
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)

    logger.info("social post generated", repo=repo.name, platform=platform, tone=tone)
    return post


async def list_posts(session: AsyncSession, user_id: Any) -> list[SocialPostModel]:
    result = await session.execute(
        select(SocialPostModel).join(RepositoryModel).where(
            RepositoryModel.user_id == user_id
        ).order_by(SocialPostModel.created_at.desc())
    )
    return list(result.scalars().all())


async def approve_post(session: AsyncSession, post_id: Any, user_id: Any) -> SocialPostModel:
    result = await session.execute(
        select(SocialPostModel).join(RepositoryModel).where(
            SocialPostModel.id == post_id,
            RepositoryModel.user_id == user_id,
        )
    )
    post = result.scalar_one_or_none()
    if post is None:
        raise NotFoundError(f"Post {post_id} not found")
    post.status = "approved"
    await session.commit()
    await session.refresh(post)
    return post
