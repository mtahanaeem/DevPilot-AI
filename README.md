<div align="center">

# 🤖 DevPilot AI

**Local-First AI-Powered GitHub Portfolio Growth Agent**

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3-F97316?logo=groq&logoColor=white)](https://groq.com)
[![n8n](https://img.shields.io/badge/n8n-1.0-EA4B71?logo=n8n&logoColor=white)](https://n8n.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## 📋 Overview

DevPilot AI is a self-hosted automation platform that helps developers grow and maintain their GitHub portfolio. Monitor repositories, generate AI-powered READMEs and documentation, optimize your resume, draft LinkedIn/Twitter posts, analyze skill gaps, plan learning, practice interviews, find open-source issues, and track career analytics — all running on your machine via a single Docker Compose command.

| Module | Description |
|:------:|:------------|
| **📦 Repo Monitor** | Sync & track GitHub repositories, detect stale repos |
| **📝 README Generator** | AI-generated READMEs with review/approve/commit workflow |
| **📄 Doc Generator** | Generate CONTRIBUTING.md and ARCHITECTURE.md |
| **📁 Portfolio** | Auto-maintained portfolio with JSON/Markdown/HTML export |
| **📋 Resume Optimizer** | Score & optimize resumes against job descriptions |
| **🐦 Social Posts** | Draft LinkedIn/Twitter posts with emojis & hashtags |
| **🔍 Skill Gaps** | Infer skills from repos, analyze gaps against job targets |
| **📚 Learning Planner** | Generate structured 4-week learning plans with tracking |
| **🎙️ Interview Generator** | Generate role-specific questions with model answers |
| **🌐 Open Source Finder** | Search & bookmark good-first-issues matching your stack |
| **📊 Analytics** | Career dashboard with stats, language distribution, weekly reports |
| **🔔 Notifications** | In-app notification center |

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Download |
|:------------|:-------:|:---------|
| Docker Desktop | 24+ | [docker.com](https://www.docker.com/products/docker-desktop) |
| Git | 2.x | [git-scm.com](https://git-scm.com) |
| Groq/OpenAI API Key | Free | [Groq](https://console.groq.com) or [OpenAI](https://platform.openai.com) |

### Setup

```bash
# Clone the repository
git clone https://github.com/mtahanaeem/DevPilot-AI.git
cd DevPilot-AI

# Configure secrets
cp .env.example .env

# Edit .env — set your LLM provider and API key:
#   LLM_PROVIDER=groq
#   GROQ_API_KEY=gsk_...

# Start the stack
docker compose up -d

# Open the dashboard
open http://localhost:80
```

---

## 🏗️ Architecture

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
                     │ GitHub API  │      │  Groq/OpenAI │   │ Notification │
                     │             │      │  Inference   │   │  Channels    │
                     └─────────────┘      └──────────────┘   └──────────────┘

              All routed through Nginx; pgAdmin for database inspection.
```

### Container Stack

| Container | Purpose |
|:----------|:--------|
| **postgres** | Primary relational database |
| **redis** | Caching + task queue |
| **qdrant** | Vector database for semantic search |
| **n8n** | Workflow automation (scheduled/event-driven) |
| **fastapi** | Backend API — Clean Architecture, async-first |
| **frontend** | React 19 + TypeScript + Tailwind CSS |
| **nginx** | Reverse proxy / routing |
| **pgadmin** | Database administration UI |

---

## 🧠 How It Works

```
GitHub Sync → Auto-detect Jobs → AI Modules → Dashboard
     │                              │
     ▼                              ▼
 Repositories                  README Generator
 Language Stats                Resume Optimizer
 Commit History                Social Post Generator
 Stale Detection               Skill Gap Analyzer
                               Learning Planner
                               Interview Generator
                               Open Source Finder
                                   │
                                   ▼
                            Analytics Reports
                            Notifications
```

| Step | Component | What It Does |
|:----:|:----------|:-------------|
| 1 | **GitHub Sync** | OAuth/PAT login syncs all repos with metadata |
| 2 | **Auto-Detect** | LLM analyzes your tech stack, generates 3 matching job descriptions |
| 3 | **AI Modules** | Each module uses the configured LLM provider for generation |
| 4 | **Dashboard** | Review, approve, and manage everything from the UI |
| 5 | **Automation** | n8n workflows run scheduled tasks (health checks, stale detection, reports) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|:------|:-----------|
| **Frontend** | React 19, TypeScript 5, Vite 5, Tailwind CSS 3, React Router 7 |
| **Backend** | Python 3.12, FastAPI 0.115, SQLAlchemy 2.0 (async), Alembic |
| **Database** | PostgreSQL 16, Redis 7, Qdrant 1.12 |
| **AI** | Groq (default), OpenAI, Anthropic, OpenRouter — swappable via `.env` |
| **Automation** | n8n 1.0 — 4 production workflows |
| **Infrastructure** | Docker Compose, Nginx, pgAdmin 4 |

---

## 🔌 API Endpoints

| Method | Endpoint Group | Description |
|:------:|:---------------|:------------|
| `POST` | `/auth/*` | GitHub OAuth/PAT login |
| `GET/POST` | `/repositories/*` | List, sync, flag stale repos |
| `GET/POST` | `/documents/*` | Generate, approve README/docs |
| `GET` | `/portfolio/*` | View & export portfolio |
| `GET/POST` | `/resume/*` | Upload resume, manage jobs, optimize, score |
| `POST` | `/social/*` | Generate LinkedIn/Twitter posts |
| `GET/POST` | `/skills/*` | Infer skills, analyze gaps |
| `GET/POST` | `/learning-plan/*` | Generate & track learning plans |
| `GET/POST` | `/interview/*` | Generate questions, answer, model answers |
| `GET/POST` | `/opensource/*` | Search issues, bookmark, dismiss |
| `GET` | `/analytics/*` | Dashboard stats, weekly reports |
| `GET/POST` | `/notifications/*` | List, mark read |
| `GET` | `/health` | Service health check |

---

## 📁 Project Structure

```
DevPilot-AI/
├── 🖥️ backend/                          # FastAPI (Clean Architecture)
│   ├── app/
│   │   ├── application/services/        # Business logic (12 modules)
│   │   ├── infrastructure/              # DB, GitHub, LLM provider
│   │   ├── presentation/routers/        # REST endpoints
│   │   └── core/                        # Config, security, logging
│   ├── alembic/                         # Database migrations
│   └── Dockerfile
│
├── 🎨 frontend/                         # React 19 + TypeScript
│   ├── src/
│   │   ├── pages/                       # 13 route pages
│   │   ├── components/                  # Layout, ProtectedRoute
│   │   ├── api/                         # API client modules
│   │   └── context/                     # Auth context
│   └── Dockerfile
│
├── ⚙️ n8n/                              # n8n workflow JSON exports
│   ├── health-monitor.json
│   ├── repository-monitor.json
│   ├── readme-auto-generator.json
│   └── weekly-career-report.json
│
├── 🔄 nginx/nginx.conf                  # Reverse proxy config
├── 📦 docker-compose.yml                # Single-command orchestration
├── 🔐 .env.example                      # Environment config template
└── 📄 DevPilot_AI_SRS.md                # Full specification
```

---

## 📊 Key Features

1. **🎯 Fully Automated** — From repo sync to README commit, the pipeline runs end-to-end
2. **🧠 LLM-Agnostic** — Swap between Groq, OpenAI, Anthropic, or OpenRouter with one `.env` line
3. **🏠 100% Local** — Everything runs on your machine, no cloud dependencies beyond GitHub/LLM APIs
4. **🔌 12 Integrated Modules** — All career tools in one dashboard with shared data
5. **⚡ Single Command** — `docker compose up -d` starts all 8 containers
6. **🔄 n8n Automation** — Scheduled workflows for health monitoring, stale detection, weekly reports
7. **🔐 Secrets-Safe** — No hardcoded credentials, all via `.env`

---

## 🤝 Connect

<div align="center">

[![GitHub](https://img.shields.io/badge/GitHub-mtahanaeem-181717?logo=github)](https://github.com/mtahanaeem)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?logo=linkedin)](https://linkedin.com/in/mtahanaeem)

**If you find this project useful, consider giving it a ⭐!**

</div>

---

<div align="center">

*Built with ❤️ using FastAPI, React, and Docker*

</div>
