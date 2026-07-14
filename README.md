# DevPilot AI

Local-first AI-powered GitHub Portfolio Growth Agent.

Monitor repositories, generate READMEs and docs, optimize your resume, draft social posts, analyze skill gaps, plan learning, practice interviews, find open-source issues, and track career analytics — all running on your machine via Docker Compose.

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url> && cd DevPilot_AI

# 2. Configure secrets
cp .env.example .env
# Edit .env — at minimum set LLM_PROVIDER and *_API_KEY

# 3. Start the stack
docker compose up -d

# 4. Open the dashboard
open http://localhost:80
```

## Architecture

| Container   | Purpose                          |
|-------------|----------------------------------|
| `postgres`  | Primary relational database      |
| `redis`     | Caching + job queue              |
| `qdrant`    | Vector database for embeddings   |
| `n8n`       | Workflow automation engine       |
| `fastapi`   | Backend API (Clean Architecture) |
| `frontend`  | React + TypeScript + Tailwind    |
| `nginx`     | Reverse proxy                    |
| `pgadmin`   | Database admin UI                |

## Documentation

Full requirements in [DevPilot_AI_SRS.md](DevPilot_AI_SRS.md).

## License

MIT
