# Project Layout

## Overview

iChrisBirch is a monorepo with a multi-service architecture: FastAPI backend (API), Vue 3 frontend, Streamlit chat interface, and APScheduler service.

## Directory Structure

```text
ichrisbirch/
├── ichrisbirch/              # Python application code
│   ├── api/                  # FastAPI backend (endpoints, middleware, auth)
│   ├── app/                  # (removed — Flask frontend fully replaced by Vue)
│   ├── chat/                 # Streamlit chat interface
│   ├── scheduler/            # APScheduler background jobs
│   ├── models/               # SQLAlchemy ORM models (shared)
│   ├── schemas/              # Pydantic schemas (shared)
│   ├── database/             # Database session management
│   ├── alembic/              # Database migrations
│   └── config.py             # Centralized settings
├── frontend/                 # Vue 3 frontend (TypeScript, Vite)
│   ├── src/
│   │   ├── api/              # Axios client, ApiError, type interfaces
│   │   ├── assets/sass/      # SCSS (ITCSS architecture)
│   │   ├── components/       # Reusable Vue components
│   │   ├── composables/      # Vue composables
│   │   ├── stores/           # Pinia stores (state management)
│   │   ├── utils/            # consola logger, helpers
│   │   ├── views/            # Page-level view components
│   │   └── router.ts         # Vue Router configuration
│   ├── e2e/                  # Playwright E2E tests
│   ├── package.json          # npm dependencies and scripts
│   └── vite.config.ts        # Vite build configuration
├── tests/                    # Python test suite (77+ files)
│   ├── conftest.py           # Pytest fixtures (session/module/function scoped)
│   ├── ichrisbirch/          # Tests mirror source structure
│   └── test_data/            # Faker-based test data generation
├── deploy-containers/        # Docker deployment configs
│   └── traefik/              # Traefik reverse proxy
│       ├── certs/            # SSL certificates (mkcert for dev)
│       ├── dynamic/          # Dynamic config (CORS, auth, security)
│       └── scripts/          # Certificate management
├── docs/                     # MkDocs documentation
├── scripts/                  # Utility scripts (backup, restore)
├── cli/icb           # Main CLI tool
├── docker-compose.yml        # Production config
├── docker-compose.dev.yml    # Development overrides (incl. Vue + path routing)
├── docker-compose.test.yml   # Testing overrides
├── Dockerfile                # Multi-stage build (Python services)
├── pyproject.toml            # Python dependencies (uv)
└── .pre-commit-config.yaml   # Quality gates (Python + Vue hooks)
```

## Environment Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (from `.env.example` for dev, SOPS-decrypted for prod) |
| `secrets/secrets.prod.enc.env` | Production secrets (SOPS + age encrypted) |
| `secrets/secrets.test.enc.env` | Testing secrets (SOPS + age encrypted) |

## Configuration

Centralized in `ichrisbirch/config.py` with nested Pydantic settings classes. Environment detection via `ENVIRONMENT` variable (`development`, `testing`, `production`).
