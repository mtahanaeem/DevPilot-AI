from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.core.exceptions import NotFoundError
from app.infrastructure.database.models.document import GeneratedDocumentModel
from app.infrastructure.database.models.repository import RepositoryModel
from app.infrastructure.github import GitHubClient
from app.infrastructure.llm import get_llm_provider

logger = get_logger()

README_SYSTEM_PROMPT = """You are a technical documentation expert. Generate a README.md for the given GitHub repository. Follow this structure:

1. **Title** – Repository name
2. **Description** – One-paragraph overview of what the project does
3. **Features** – Bullet list of key features
4. **Tech Stack** – Languages, frameworks, tools used
5. **Installation** – Step-by-step setup instructions
6. **Usage** – Basic usage examples
7. **Project Structure** – Brief overview of the codebase layout
8. **Screenshots** – Placeholder section
9. **Contributing** – How to contribute (generic)
10. **License** – Placeholder

Use GitHub-flavored Markdown. Be concise but informative."""

CONTRIBUTING_SYSTEM_PROMPT = """You are a technical documentation expert. Generate a CONTRIBUTING.md for the given GitHub repository. Follow this structure:

1. **Welcome** – Brief welcome and why contributions are valued
2. **Code of Conduct** – Link to generic Code of Conduct
3. **Getting Started** – How to set up the development environment
4. **Development Workflow** – Branching strategy, commit conventions, PR process
5. **Coding Standards** – Linting, formatting, testing requirements
6. **Pull Request Checklist** – Steps before submitting a PR
7. **Issue Reporting** – How to report bugs or request features

Use GitHub-flavored Markdown. Be friendly and welcoming."""

ARCHITECTURE_SYSTEM_PROMPT = """You are a software architect. Generate an ARCHITECTURE.md for the given GitHub repository. Follow this structure:

1. **Overview** – High-level architecture description
2. **Tech Stack** – Languages, frameworks, databases, infrastructure
3. **Directory Structure** – Explanation of key directories and their purpose
4. **Core Components** – Major modules/services and their responsibilities
5. **Data Flow** – How data moves through the system
6. **Key Design Decisions** – Rationale for important architectural choices
7. **Diagrams** – Placeholder for architecture diagrams

Use GitHub-flavored Markdown. Be technical and precise."""

SYSTEM_PROMPTS = {
    "readme": README_SYSTEM_PROMPT,
    "contributing": CONTRIBUTING_SYSTEM_PROMPT,
    "architecture": ARCHITECTURE_SYSTEM_PROMPT,
}

DOC_PROMPT_TEMPLATES = {
    "readme": """Repository: {name}
Description: {description}
Language: {language_stats}
Stars: {stars} | Forks: {forks}

Top-level files:
{file_list}

Key dependency files:
{deps_content}

Generate a professional README.md for this project.""",

    "contributing": """Repository: {name}
Description: {description}
Language: {language_stats}

Top-level files:
{file_list}

Dependency files:
{deps_content}

Generate a CONTRIBUTING.md for contributors to this project.""",

    "architecture": """Repository: {name}
Description: {description}
Language: {language_stats}
Stars: {stars} | Forks: {forks}

Top-level files:
{file_list}

Dependency files:
{deps_content}

Generate an ARCHITECTURE.md documenting the system architecture of this project.""",
}


async def _get_repo_data(session: AsyncSession, user_id: Any, repo_id: Any, pat: str) -> RepositoryModel:
    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.id == repo_id, RepositoryModel.user_id == user_id)
    )
    repo = result.scalar_one_or_none()
    if repo is None:
        raise NotFoundError(f"Repository {repo_id} not found")

    client = GitHubClient(token=pat)
    try:
        file_tree = await client.get_repo_contents(repo.owner, repo.name)
    finally:
        await client.close()

    repo.file_tree = file_tree
    return repo


async def generate_document(
    session: AsyncSession, user_id: Any, repo_id: Any, pat: str, doc_type: str = "readme"
) -> GeneratedDocumentModel:
    if doc_type not in SYSTEM_PROMPTS:
        raise ValueError(f"Unsupported document type: {doc_type}")

    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.id == repo_id, RepositoryModel.user_id == user_id)
    )
    repo = result.scalar_one_or_none()
    if repo is None:
        raise NotFoundError(f"Repository {repo_id} not found")

    client = GitHubClient(token=pat)
    try:
        file_tree = await client.get_repo_contents(repo.owner, repo.name)
        file_list = "\n".join(f["name"] for f in file_tree if f["type"] == "file")

        deps_content = ""
        for fname in ("package.json", "requirements.txt", "Cargo.toml", "go.mod", "Gemfile"):
            try:
                deps_content += f"\n--- {fname} ---\n"
                deps_content += await client.get_file_content(repo.owner, repo.name, fname)
            except Exception:
                pass
    finally:
        await client.close()

    prompt = DOC_PROMPT_TEMPLATES[doc_type].format(
        name=repo.name,
        description=repo.description or "(none)",
        language_stats=repo.language_stats or "(unknown)",
        stars=repo.stars,
        forks=repo.forks,
        file_list=file_list,
        deps_content=deps_content,
    )

    llm = get_llm_provider()
    content = await llm.generate(prompt, system=SYSTEM_PROMPTS[doc_type], max_tokens=3072)

    doc = GeneratedDocumentModel(
        repository_id=repo.id,
        type=doc_type,
        content=content,
        status="draft",
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)

    logger.info("document generated", repo=repo.name, doc_type=doc_type, doc_id=str(doc.id))
    return doc


async def generate_readme(
    session: AsyncSession, user_id: Any, repo_id: Any, pat: str
) -> GeneratedDocumentModel:
    return await generate_document(session, user_id, repo_id, pat, "readme")


async def list_drafts(
    session: AsyncSession, user_id: Any, repo_id: str | None = None
) -> list[GeneratedDocumentModel]:
    query = select(GeneratedDocumentModel).join(RepositoryModel).where(
        RepositoryModel.user_id == user_id
    )
    if repo_id:
        query = query.where(GeneratedDocumentModel.repository_id == repo_id)
    query = query.order_by(GeneratedDocumentModel.created_at.desc())
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_document(session: AsyncSession, doc_id: Any, user_id: Any) -> GeneratedDocumentModel:
    result = await session.execute(
        select(GeneratedDocumentModel).join(RepositoryModel).where(
            GeneratedDocumentModel.id == doc_id,
            RepositoryModel.user_id == user_id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise NotFoundError(f"Document {doc_id} not found")
    return doc


async def approve_document(
    session: AsyncSession, doc_id: Any, user_id: Any, pat: str
) -> GeneratedDocumentModel:
    doc = await get_document(session, doc_id, user_id)
    if doc.status != "draft":
        raise ValueError(f"Document is already {doc.status}")

    result = await session.execute(
        select(RepositoryModel).where(RepositoryModel.id == doc.repository_id)
    )
    repo = result.scalar_one_or_none()
    if repo is None:
        raise NotFoundError(f"Repository {doc.repository_id} not found")

    filename_map = {
        "readme": "README.md",
        "contributing": "CONTRIBUTING.md",
        "architecture": "ARCHITECTURE.md",
    }
    filename = filename_map.get(doc.type, f"{doc.type}.md")

    client = GitHubClient(token=pat)
    try:
        await client.create_or_update_file(repo.owner, repo.name, filename, f"docs: add {filename}", doc.content)
        doc.status = "committed"
    except Exception as exc:
        logger.error("commit failed", exc_info=exc, repo=f"{repo.owner}/{repo.name}")
        doc.status = "approved"
    finally:
        await client.close()

    await session.commit()
    await session.refresh(doc)
    logger.info("document committed", doc_id=str(doc.id), filename=filename)
    return doc


async def regenerate_document(
    session: AsyncSession, doc_id: Any, user_id: Any, feedback: str
) -> GeneratedDocumentModel:
    doc = await get_document(session, doc_id, user_id)
    system_prompt = SYSTEM_PROMPTS.get(doc.type, README_SYSTEM_PROMPT)

    llm = get_llm_provider()
    prompt = f"""Previous version:
{doc.content}

Feedback for revision:
{feedback}

Please revise the document based on the feedback above."""

    new_content = await llm.generate(prompt, system=system_prompt, max_tokens=3072)
    doc.content = new_content
    doc.status = "draft"
    await session.commit()
    await session.refresh(doc)
    return doc
