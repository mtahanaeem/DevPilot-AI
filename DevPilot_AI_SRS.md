# Software Requirements Specification (SRS)
## DevPilot AI — Local-First AI-Powered GitHub Portfolio Growth Agent

**Version:** 1.0
**Date:** July 14, 2026
**Document Type:** Software Requirements Specification (IEEE 830-inspired)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the functional and non-functional requirements for **DevPilot AI**, a self-hosted automation platform that helps software developers grow and maintain their GitHub portfolio using AI-generated documentation, career analytics, and workflow automation. This SRS is written to be consumed directly by a coding agent (e.g., OpenCode CLI) as a build specification, and by a human engineer as a reference architecture document.

### 1.2 Scope

DevPilot AI monitors a developer's GitHub repositories and automatically:

- Generates and updates READMEs and documentation
- Publishes portfolio updates
- Optimizes resumes against job descriptions
- Drafts LinkedIn/Twitter posts about new work
- Analyzes skill gaps and produces learning plans
- Generates mock interview questions
- Recommends open-source issues to contribute to
- Surfaces career analytics on a dashboard
- Sends notifications across channels

The system runs entirely on the user's local machine via Docker Compose, with all AI text-generation calls routed through a **hosted inference API (Groq or OpenAI)** rather than a local model — see §3.5 for rationale.

### 1.3 Intended Audience

- The coding agent generating the implementation
- The developer (Muhammad) maintaining and extending the system
- Any future contributor reviewing the architecture

### 1.4 Definitions

| Term | Meaning |
|---|---|
| SRS | Software Requirements Specification |
| n8n | Open-source workflow automation tool |
| Qdrant | Vector database for embeddings/semantic search |
| Groq | Hosted LPU-based LLM inference API (fast, low-cost) |
| PAT | GitHub Personal Access Token |
| SSE | Server-Sent Events |

### 1.5 Document Conventions

Each functional requirement is tagged `FR-<module>-<n>`. Each non-functional requirement is tagged `NFR-<n>`. Priority: **Must** (M), **Should** (S), **Could** (C) — MoSCoW method.

---

## 2. Overall Description

### 2.1 Product Perspective

DevPilot AI is a new, standalone, local-first system. It is not a SaaS product — no multi-tenant concerns, no external hosting requirement. It integrates with GitHub via OAuth/PAT and with an LLM provider via API key.

### 2.2 Product Functions (Summary)

1. GitHub Repository Monitor
2. AI README Generator
3. Documentation Generator
4. Portfolio Updater
5. Resume Optimizer
6. LinkedIn/Twitter Post Generator
7. Skill Gap Analyzer
8. Learning Planner
9. Interview Question Generator
10. Open Source Issue Finder
11. Career Analytics Dashboard
12. Notification Center

### 2.3 User Classes

- **Primary user (owner-operator):** a single developer running the stack locally to manage their own portfolio. No multi-user auth complexity is required for v1, though the schema should not preclude it later.

### 2.4 Operating Environment

- Windows 11 + WSL2
- Docker Desktop (Docker Compose v2)
- Intel i9-14900HX, RTX 4060 Laptop GPU (GPU is *not* required by this spec since inference is API-based, but remains available for optional local embedding acceleration)
- 16–32 GB RAM
- 1 TB SSD

### 2.5 Design and Implementation Constraints

- Everything must be startable with a single command: `docker compose up -d`
- No dependency on paid infrastructure beyond the chosen LLM API's free/pay-as-you-go tier
- Clean Architecture / SOLID / modular, async-first backend
- All secrets via `.env`, never hardcoded

### 2.6 Assumptions and Dependencies

- User has a GitHub account and can generate a PAT or configure an OAuth App
- User has an API key for at least one supported LLM provider (see §3.5)
- Internet access is required for GitHub API calls and LLM API calls (this is **not** a fully offline system, since local inference has been removed)

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│   React     │────▶│   FastAPI    │────▶│   PostgreSQL   │
│  Dashboard  │◀────│   Backend    │◀────│    Database    │
└─────────────┘     └──────┬───────┘     └────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   ┌─────────┐        ┌───────────┐       ┌───────────┐
   │  Redis  │        │  Qdrant   │       │    n8n    │
   │ (cache/ │        │  (vector  │       │ (workflow │
   │  queue) │        │  search)  │       │  engine)  │
   └─────────┘        └───────────┘       └─────┬─────┘
                                                  │
                            ┌─────────────────────┼──────────────────┐
                            ▼                     ▼                  ▼
                     ┌─────────────┐      ┌──────────────┐   ┌──────────────┐
                     │ GitHub API  │      │  Groq / OpenAI│   │ Notification │
                     │             │      │  Inference API│   │  Channels    │
                     └─────────────┘      └──────────────┘   └──────────────┘

                     All routed through Nginx reverse proxy; pgAdmin for DB inspection.
```

### 3.2 Architectural Style

- **Backend:** Clean Architecture — domain / application / infrastructure / presentation layers
- **Communication:** REST (FastAPI) for synchronous calls; n8n webhooks for event-driven/scheduled automation; Redis pub/sub or queue for background jobs
- **Frontend:** React + TypeScript, component-driven, Tailwind CSS utility styling
- **Data:** PostgreSQL as system of record; Qdrant for semantic search over repo content/resume/job descriptions; Redis for caching and job queues

### 3.3 Container Inventory

| Container | Purpose |
|---|---|
| `postgres` | Primary relational database |
| `redis` | Caching + task queue backing store |
| `qdrant` | Vector database for embeddings |
| `n8n` | Workflow automation engine |
| `fastapi` | Backend API service |
| `frontend` | React dashboard (served via Nginx or dev server) |
| `nginx` | Reverse proxy / TLS termination / routing |
| `pgadmin` | Database administration UI |

Note: the `ollama` container present in earlier drafts is **removed**. AI text generation now calls out to an external inference API over HTTPS (see §3.5), so no local model container or GPU passthrough is required for core functionality.

### 3.4 Removal of Ollama — Rationale and Replacement

The original specification listed Ollama as the preferred inference engine, with Groq/OpenAI as optional fallbacks. This revision inverts that priority for the following reasons:

- Hosted APIs eliminate GPU/VRAM constraints and model-download time, so the project builds and runs the same way on any machine.
- Groq's inference API in particular is very low-latency and has a generous free tier, well suited to a portfolio project.
- Removing local inference simplifies the Docker Compose file (one fewer multi-GB image, no CUDA/driver considerations inside WSL2).

**Supported providers (configurable, pick one or more via `.env`):**

| Provider | Notes |
|---|---|
| **Groq** (default) | Fast Llama/Mixtral-class models, low cost, generous free tier |
| **OpenAI** | GPT-family models, broadest tooling/ecosystem support |
| **Anthropic (Claude API)** | Optional, for higher-quality long-form writing (README/docs) |
| **OpenRouter** | Optional aggregator if the user wants provider flexibility without code changes |

The backend must implement an `LLMProvider` interface (strategy pattern) so switching providers is a config change, not a code change.

### 3.5 LLM Provider Abstraction (Required Design)

```
interface LLMProvider:
    generate(prompt: str, system: str | None, max_tokens: int) -> str
    embed(text: str) -> list[float]          # for Qdrant indexing
```

Concrete implementations: `GroqProvider`, `OpenAIProvider`, `AnthropicProvider`. Selected via `LLM_PROVIDER` environment variable. Embeddings default to a hosted embeddings endpoint (e.g., OpenAI `text-embedding-3-small`) unless another is configured.

---

## 4. Functional Requirements

### 4.1 Module 1 — GitHub Repository Monitor

- **FR-GRM-1 (M):** System shall connect to GitHub via OAuth App or PAT and list the user's repositories.
- **FR-GRM-2 (M):** System shall poll (or receive webhook events for) repository changes: new commits, new releases, new stars, new issues/PRs.
- **FR-GRM-3 (M):** System shall persist repository metadata and change history in PostgreSQL.
- **FR-GRM-4 (S):** System shall detect stale repositories (no commits in N days, configurable) and flag them for review.

### 4.2 Module 2 — AI README Generator

- **FR-ARG-1 (M):** System shall generate a README draft from repository metadata, file tree, and key source files, using the configured LLM provider.
- **FR-ARG-2 (M):** User shall be able to review and approve/edit the generated README before it is committed.
- **FR-ARG-3 (M):** On approval, system shall commit the README via the GitHub API (or open a PR, configurable).
- **FR-ARG-4 (S):** Generated README shall follow a template with sections: description, features, tech stack, installation, usage, screenshots placeholder, license.

### 4.3 Module 3 — Documentation Generator

- **FR-DOC-1 (M):** System shall generate module-level and function-level documentation from source code (docstrings/JSDoc-style, language-aware).
- **FR-DOC-2 (S):** System shall generate a `CONTRIBUTING.md` and `ARCHITECTURE.md` on request.
- **FR-DOC-3 (C):** System shall generate API reference docs from FastAPI's OpenAPI schema.

### 4.4 Module 4 — Portfolio Updater

- **FR-PU-1 (M):** System shall maintain a "portfolio" data model summarizing all tracked repositories (title, description, tags, links, highlights).
- **FR-PU-2 (M):** System shall regenerate a portfolio page/section (e.g., static JSON or Markdown feed) whenever tracked repos change.
- **FR-PU-3 (S):** System shall support exporting the portfolio as JSON, Markdown, or HTML for embedding elsewhere.

### 4.5 Module 5 — Resume Optimizer

- **FR-RO-1 (M):** User shall be able to upload a resume (PDF/DOCX/text).
- **FR-RO-2 (M):** User shall be able to paste a target job description.
- **FR-RO-3 (M):** System shall use the LLM to suggest resume edits/keyword alignment against the job description, and return a diff/suggestion list (not silent overwrite).
- **FR-RO-4 (S):** System shall score resume-to-job-description match (0–100) using embedding similarity (Qdrant) plus LLM judgment.

### 4.6 Module 6 — LinkedIn/Twitter Post Generator

- **FR-SPG-1 (M):** System shall draft a social post announcing a new repository, release, or milestone.
- **FR-SPG-2 (M):** User shall be able to select tone (professional, casual, technical) and platform (LinkedIn vs. X/Twitter character limits).
- **FR-SPG-3 (C):** System shall support scheduling posts via n8n (manual copy-paste export for v1 is acceptable if no posting API is integrated).

### 4.7 Module 7 — Skill Gap Analyzer

- **FR-SGA-1 (M):** System shall infer the user's current skills from repository languages, frameworks, and commit history.
- **FR-SGA-2 (M):** System shall compare inferred skills against one or more target job descriptions and list gaps.
- **FR-SGA-3 (S):** System shall rank gaps by frequency across multiple job postings supplied by the user.

### 4.8 Module 8 — Learning Planner

- **FR-LP-1 (M):** System shall generate a structured learning plan (weekly milestones) to close identified skill gaps.
- **FR-LP-2 (S):** System shall track completion status of learning plan items.
- **FR-LP-3 (C):** System shall suggest specific resources (courses, docs, repos) per gap — LLM-generated, clearly marked as suggestions to verify.

### 4.9 Module 9 — Interview Question Generator

- **FR-IQG-1 (M):** System shall generate technical interview questions tailored to a target role/job description and the user's tracked repositories.
- **FR-IQG-2 (S):** System shall generate model answers or answer outlines for self-study.
- **FR-IQG-3 (C):** System shall support a "mock interview" mode with sequential Q&A stored per session.

### 4.10 Module 10 — Open Source Issue Finder

- **FR-OSF-1 (M):** System shall search GitHub for issues labeled `good first issue` / `help wanted` matching the user's skill profile.
- **FR-OSF-2 (S):** System shall rank matches using embedding similarity between issue text and the user's skills/interests.
- **FR-OSF-3 (C):** System shall let the user bookmark/dismiss suggested issues.

### 4.11 Module 11 — Career Analytics Dashboard

- **FR-CAD-1 (M):** Dashboard shall display commit frequency, language distribution, star/fork trends over time.
- **FR-CAD-2 (M):** Dashboard shall display a weekly/monthly career report summarizing activity and progress on learning plan items.
- **FR-CAD-3 (S):** Dashboard shall visualize skill-gap-to-learning-plan progress.

### 4.12 Module 12 — Notification Center

- **FR-NC-1 (M):** System shall notify the user (in-app + at least one external channel: email, Discord, Slack, or Telegram) when: a README/doc is generated and awaiting approval, a weekly report is ready, or a stale repo is detected.
- **FR-NC-2 (S):** User shall be able to configure notification channels and frequency per event type.
- **FR-NC-3 (C):** System shall support a digest mode (batched daily/weekly notification instead of per-event).

---

## 5. n8n Workflows

| Workflow | Trigger | Summary |
|---|---|---|
| Repository Monitor | Scheduled (e.g., hourly) / GitHub webhook | Polls/receives repo changes, writes to DB, triggers downstream workflows |
| README Generator | Manual or on new-repo detection | Calls FastAPI generation endpoint, awaits approval, commits via GitHub API |
| Documentation Generator | Manual or scheduled | Generates docs for repos flagged as outdated |
| Portfolio Sync | On repo change | Regenerates portfolio export |
| Weekly Career Report | Scheduled (weekly) | Aggregates analytics, generates summary, sends notification |
| Learning Planner | Manual or on skill-gap update | Regenerates/updates learning plan |
| Notification Service | Event-driven | Routes events to configured channels |
| Health Monitor | Scheduled | Pings all containers/services, alerts on failure |

---

## 6. External Interface Requirements

### 6.1 GitHub Integration

- OAuth App (preferred) or PAT (fallback) with scopes: `repo`, `read:user`, `read:org` (optional)
- Rate-limit aware client with exponential backoff and caching (Redis) to stay within GitHub API limits

### 6.2 LLM Provider Integration

- Configurable via `.env`: `LLM_PROVIDER=groq|openai|anthropic|openrouter`, plus `<PROVIDER>_API_KEY`
- Backend must handle provider errors/timeouts gracefully with retries and a clear user-facing error state

### 6.3 Notification Channels

- Email (SMTP), and at least one of: Discord webhook, Slack webhook, Telegram bot API — configurable

---

## 7. Data Model (Core Entities)

| Entity | Key Fields |
|---|---|
| `User` | id, github_username, oauth_token (encrypted), created_at |
| `Repository` | id, user_id, github_repo_id, name, description, language_stats, stars, forks, last_commit_at, is_stale |
| `GeneratedDocument` | id, repository_id, type (readme/docs/etc.), content, status (draft/approved/committed), created_at |
| `Resume` | id, user_id, raw_text, file_path, created_at |
| `JobDescription` | id, user_id, raw_text, source_url, created_at |
| `SkillGapReport` | id, user_id, job_description_id, gaps (jsonb), created_at |
| `LearningPlan` | id, user_id, items (jsonb), created_at |
| `InterviewSession` | id, user_id, job_description_id, questions (jsonb), answers (jsonb) |
| `SocialPost` | id, repository_id, platform, content, status |
| `Notification` | id, user_id, event_type, channel, sent_at, status |
| `AnalyticsSnapshot` | id, user_id, period, metrics (jsonb) |

Embeddings for repositories, resumes, and job descriptions are stored in Qdrant, keyed by the corresponding PostgreSQL entity ID.

---

## 8. API Endpoint Overview (FastAPI)

Grouped by resource; full OpenAPI spec to be generated from code.

- `/auth/*` — GitHub OAuth login, callback, token refresh
- `/repositories/*` — list, sync, get detail, flag stale
- `/documents/*` — generate, list drafts, approve, commit
- `/portfolio/*` — get, export (json/md/html)
- `/resume/*` — upload, optimize, score-against-job
- `/jobs/*` — submit job description, list
- `/skills/*` — gap analysis, get profile
- `/learning-plan/*` — generate, get, update item status
- `/interview/*` — generate questions, start session, submit answer
- `/opensource/*` — search matches, bookmark, dismiss
- `/analytics/*` — dashboard summary, weekly report
- `/notifications/*` — list, configure channels, mark read
- `/health` — service health check

Target: **45–55 endpoints** across these groups, consistent with the original project scope.

---

## 9. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | Entire stack shall start via `docker compose up -d` with no manual post-start steps beyond `.env` configuration |
| NFR-2 | Backend endpoints shall respond within 2s for non-LLM operations (p95) |
| NFR-3 | LLM-backed operations shall show a loading/progress state in the UI and support cancellation where feasible |
| NFR-4 | All secrets (API keys, OAuth tokens) shall be stored via environment variables / encrypted at rest, never logged |
| NFR-5 | System shall degrade gracefully if the LLM API is unreachable (queue the request, surface a clear error, do not crash the workflow) |
| NFR-6 | Codebase shall follow Clean Architecture and SOLID principles, with dependency injection for provider swapping |
| NFR-7 | Backend shall be async end-to-end (FastAPI async routes, async DB driver) |
| NFR-8 | All containers shall define health checks in Docker Compose |
| NFR-9 | System shall include structured logging (JSON logs) for backend and n8n workflows |
| NFR-10 | Test coverage target: ≥70% for backend business logic (unit) plus integration tests for critical workflows |

---

## 10. Development Phases (Recommended Build Order)

Given the scope (~80–120 n8n nodes, ~45–55 API endpoints, ~15–20 Docker/config files, tens of thousands of lines of code), the project should be built incrementally rather than in one generation pass. Recommended phases:

1. **Project scaffolding & Docker Compose** — all containers defined and healthy, no business logic yet
2. **Database layer** — schema, migrations, seed data
3. **FastAPI backend core** — auth, repository monitor, LLM provider abstraction
4. **GitHub integration** — OAuth/PAT flow, repo sync, webhook handling
5. **AI content modules** — README/doc generator, resume optimizer, social post generator
6. **n8n workflows** — wire up scheduled/event-driven automation calling the backend
7. **React dashboard** — auth, repo list, document review/approval UI, analytics views
8. **Career intelligence modules** — skill gap, learning planner, interview generator, open-source finder
9. **Notifications** — channel integrations, event routing
10. **Testing, hardening, documentation & installation guide**

Each phase should conclude with: a summary of what was built, a file tree, and an explicit "next phase" pointer — so the coding agent maintains continuity across sessions instead of losing context in a single mega-prompt.

---

## 11. Deliverables

- `docker-compose.yml` + per-service `Dockerfile`s
- Backend source (FastAPI, Clean Architecture layout)
- Frontend source (React + TypeScript + Tailwind)
- n8n workflow JSON exports
- Database migrations (Alembic or equivalent)
- API documentation (auto-generated OpenAPI + a written overview)
- `README.md` for the overall project
- `.env.example` with every required variable documented
- Installation/setup guide (step-by-step, Windows/WSL2-specific notes)

---

## 12. Success Criteria

- Full stack starts cleanly with `docker compose up -d` on the specified hardware
- A user can connect a GitHub account, sync repositories, and generate/approve/commit a README end-to-end
- At least one non-README AI module (resume optimizer, skill gap analyzer, or interview generator) is fully functional
- Dashboard displays real analytics pulled from the user's own GitHub data
- No hardcoded secrets; switching LLM provider is a one-line `.env` change

---

## Appendix A — Descope / Cut List (If Time Runs Short)

The full 12-module scope is the target, but if time pressure hits mid-build,
descope in this order — each tier can be dropped without breaking the
modules above it, since nothing below depends on them:

**Tier 1 — cut first (lowest cost to remove, least central to the core story):**
- Module 6: LinkedIn/Twitter Post Generator
- Module 10: Open Source Issue Finder

**Tier 2 — cut second (valuable but not load-bearing):**
- Module 9: Interview Question Generator
- Module 8: Learning Planner

**Tier 3 — cut only if truly necessary (these underpin the "career intelligence" half of the pitch):**
- Module 7: Skill Gap Analyzer
- Module 5: Resume Optimizer

**Never cut — these are the core end-to-end story and the minimum viable demo:**
- Module 1: GitHub Repository Monitor
- Module 2: AI README Generator
- Module 4: Portfolio Updater
- Module 11: Career Analytics Dashboard
- Module 12: Notification Center (at minimum, one channel)

Dropping Tier 1–3 also lets you drop Qdrant (no embedding-backed modules
left) and simplify the n8n workflow count accordingly — note this in your
final documentation as "future work" rather than silently omitting it, so
reviewers see it as a scoping decision, not an unfinished feature.

## Appendix B — Environment Variables (`.env.example` contents to generate)

```
# GitHub
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_PAT=

# LLM Provider (choose one as default)
LLM_PROVIDER=groq
GROQ_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OPENROUTER_API_KEY=

# Embeddings
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small

# Database
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=devpilot

# Redis
REDIS_URL=redis://redis:6379

# Qdrant
QDRANT_URL=http://qdrant:6333

# Notifications
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
DISCORD_WEBHOOK_URL=
SLACK_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=

# App
JWT_SECRET=
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```
