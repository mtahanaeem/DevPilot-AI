from __future__ import annotations

import base64
import time
from typing import Any, Optional

import httpx
from structlog import get_logger

from app.core.config import settings

logger = get_logger()


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None) -> None:
        self.token = token or settings.GITHUB_PAT or ""
        self._client: Optional[httpx.AsyncClient] = None
        self._remaining: int = 60
        self._reset_at: float = 0.0

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "DevPilot-AI/1.0",
                },
                timeout=30.0,
                event_hooks={"response": [self._rate_limit_hook]},
            )
        return self._client

    async def _rate_limit_hook(self, response: httpx.Response) -> None:
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_at = response.headers.get("X-RateLimit-Reset")
        if remaining is not None:
            self._remaining = int(remaining)
        if reset_at is not None:
            self._reset_at = float(reset_at)

        if self._remaining == 0:
            wait = max(1.0, self._reset_at - time.time() + 1.0)
            logger.warning("rate limit hit, sleeping", wait_seconds=round(wait))
            time.sleep(wait)

    async def _paginate(self, path: str, **params: Any) -> list[dict]:
        client = await self._get_client()
        items: list[dict] = []
        page = 1
        while True:
            resp = await client.get(path, params={"per_page": 100, "page": page, **params})
            resp.raise_for_status()
            page_items = resp.json()
            if not page_items:
                break
            items.extend(page_items)
            page += 1
        return items

    async def get_user_repos(self) -> list[dict]:
        return await self._paginate("/user/repos", sort="pushed")

    async def get_repo(self, owner: str, repo: str) -> dict:
        client = await self._get_client()
        resp = await client.get(f"/repos/{owner}/{repo}")
        resp.raise_for_status()
        return resp.json()

    async def get_repo_contents(self, owner: str, repo: str, path: str = "") -> list[dict]:
        client = await self._get_client()
        resp = await client.get(f"/repos/{owner}/{repo}/contents/{path}")
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else [data]

    async def get_file_content(self, owner: str, repo: str, path: str) -> str:
        client = await self._get_client()
        resp = await client.get(f"/repos/{owner}/{repo}/contents/{path}")
        resp.raise_for_status()
        data = resp.json()
        content = data.get("content", "")
        if not content:
            return ""
        return base64.b64decode(content).decode("utf-8")

    async def create_or_update_file(
        self, owner: str, repo: str, path: str, message: str, content: str, sha: Optional[str] = None
    ) -> dict:
        client = await self._get_client()
        body: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
        }
        if sha:
            body["sha"] = sha

        resp = await client.put(f"/repos/{owner}/{repo}/contents/{path}", json=body)
        resp.raise_for_status()
        return resp.json()

    async def create_blob(self, owner: str, repo: str, content: str) -> str:
        client = await self._get_client()
        resp = await client.post(
            f"/repos/{owner}/{repo}/git/blobs",
            json={"content": content, "encoding": "utf-8"},
        )
        resp.raise_for_status()
        return resp.json()["sha"]

    async def get_ref(self, owner: str, repo: str, ref: str = "heads/main") -> dict:
        client = await self._get_client()
        resp = await client.get(f"/repos/{owner}/{repo}/git/ref/{ref}")
        resp.raise_for_status()
        return resp.json()

    async def create_tree(
        self, owner: str, repo: str, base_tree: str, blobs: list[dict[str, Any]]
    ) -> str:
        client = await self._get_client()
        resp = await client.post(
            f"/repos/{owner}/{repo}/git/trees",
            json={"base_tree": base_tree, "tree": blobs},
        )
        resp.raise_for_status()
        return resp.json()["sha"]

    async def create_commit(
        self, owner: str, repo: str, message: str, tree_sha: str, parent_sha: str
    ) -> dict:
        client = await self._get_client()
        resp = await client.post(
            f"/repos/{owner}/{repo}/git/commits",
            json={"message": message, "tree": tree_sha, "parents": [parent_sha]},
        )
        resp.raise_for_status()
        return resp.json()

    async def update_ref(self, owner: str, repo: str, ref: str, sha: str) -> dict:
        client = await self._get_client()
        resp = await client.patch(
            f"/repos/{owner}/{repo}/git/refs/{ref}",
            json={"sha": sha, "force": False},
        )
        resp.raise_for_status()
        return resp.json()

    async def list_webhooks(self, owner: str, repo: str) -> list[dict]:
        client = await self._get_client()
        resp = await client.get(f"/repos/{owner}/{repo}/hooks")
        resp.raise_for_status()
        return resp.json()

    async def create_webhook(
        self, owner: str, repo: str, url: str, secret: str
    ) -> dict:
        client = await self._get_client()
        resp = await client.post(
            f"/repos/{owner}/{repo}/hooks",
            json={
                "name": "web",
                "active": True,
                "events": ["push", "release", "pull_request", "issues", "star"],
                "config": {
                    "url": url,
                    "content_type": "json",
                    "secret": secret,
                    "insecure_ssl": "0",
                },
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def delete_webhook(self, owner: str, repo: str, hook_id: int) -> None:
        client = await self._get_client()
        resp = await client.delete(f"/repos/{owner}/{repo}/hooks/{hook_id}")
        resp.raise_for_status()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def search_issues(self, query: str, limit: int = 20) -> list[dict]:
        client = await self._get_client()
        resp = await client.get("/search/issues", params={"q": query, "per_page": min(limit, 100), "sort": "stars"})
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        results = []
        for item in items[:limit]:
            repo_full = item.get("repository_url", "").replace("https://api.github.com/repos/", "")
            owner, repo = repo_full.split("/") if "/" in repo_full else ("", "")
            results.append({
                "id": item["number"],
                "owner": owner,
                "repo": repo,
                "title": item["title"],
                "html_url": item["html_url"],
                "labels": [l["name"] for l in item.get("labels", [])],
                "score": item.get("score", 0),
                "state": item.get("state", "open"),
            })
        return results
