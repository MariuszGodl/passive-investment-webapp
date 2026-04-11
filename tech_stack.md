# Project Tech Stack

## Other
- **pre-commit** – For code quality and automated hooks.
- **changelog** – To manage project release notes and versioning.
- **alembic** – For database migrations.
- **dotenv** – Manage environment variables securely.

## Data Storage
- **PostgresDB** – Relational database for structured data.
- **ORM** – `SQLAlchemy` for mapping Python objects to database tables.
- **Connection Pooling** – (Oprional) `asyncpg` (async) or `psycopg2` (sync) for efficient database connections.

## Web Application
- **FastAPI** – Modern, asynchronous web framework for building APIs.
- **Server** – `Uvicorn` (ASGI) or `Gunicorn + Uvicorn workers` for production deployment.
- **Authentication & Security** – (Optional) JWT, OAuth2, or `FastAPI Users`.
- **Validation & Docs** – Pydantic models, automatic Swagger/OpenAPI docs or FastAPI.

## Data Retrieval
- **Selenium/Playwright/requests** – or  For scraping dynamic web pages.
- **Dagster** – (Optional) Orchestration and scheduling of scraping/data pipelines using sensors or schedulers.
- **Data Cleaning** – `pandas` for transforming and cleaning scraped data.
- **Retry / Error Handling** – (Optional) `tenacity` for retries on failed tasks.

## Asynchronous Task Queue (Optional)
- **RabbitMQ** – Message broker to decouple scraping tasks from API responses.
- **Celery** – Background worker to process tasks from RabbitMQ asynchronously.

## Caching & Performance (Optional)
- **Redis** – For caching API responses or temporary scraped data.

## DevOps / CI-CD
- **Docker** – Containerization for reproducible dev/prod environments.
- **CI/CD Pipelines** – GitHub Actions, GitLab CI, or similar for automated testing and deployment.
- **Testing** – `pytest` for unit tests; `pytest-asyncio` for async code testing.

## Observability & Monitoring (Optional)
- **Logging** – `structlog` or Python `logging` with rotation.
- **Monitoring / Metrics** – Prometheus + Grafana for API and pipeline monitoring.
- **Error Tracking** – Sentry or similar tools for real-time error reporting.

## RAG Chatbot (Optional / Advanced)


my_project/
├── .env
│   # Environment variables (DB URL, secrets, API keys)
│   # NEVER commit real values

├── .gitignore
│   # Ignore venvs, __pycache__, .env, data dumps, etc.

├── .pre-commit-config.yaml
│   # Automated code quality (black, isort, flake8, etc.)

├── CHANGELOG.md
│   # Track releases, changes, breaking updates

├── docker-compose.yml
│   # Main orchestration (API, DB, Redis, worker, etc.)
│   # Production-like configuration

├── Makefile
│   # Developer shortcuts:
│   # make run, make migrate, make test, etc.

├── services/
│   └── api/
│       ├── Dockerfile
│       │   # Builds API + worker image
│       │   # Shared between FastAPI and Celery

│       ├── pyproject.toml
│       │   # Python dependencies (FastAPI, SQLAlchemy, Celery, etc.)
│       │   # Poetry config (package-mode=false recommended)

│       ├── alembic.ini
│       │   # Alembic configuration (DB migrations)

│       ├── alembic/
│       │   ├── versions/
│       │   │   # Migration history (auto-generated)
│       │   │   # THIS = source of truth for DB schema evolution
│       │   └── env.py
│       │       # Alembic runtime config (connects to DB)

│       ├── app/
│       │   ├── main.py
│       │   │   # FastAPI entrypoint
│       │   │   # App initialization, middleware, routers

│       │   ├── api/
│       │   │   └── v1/
│       │   │       └── router.py
│       │   │           # API routes grouped by version
│       │   │           # Example: /api/v1/users

│       │   ├── core/
│       │   │   ├── config.py
│       │   │   │   # App configuration (env vars, settings)
│       │   │   │   # Use Pydantic BaseSettings

│       │   │   ├── db.py
│       │   │   │   # SQLAlchemy engine + session setup
│       │   │   │   # Async engine recommended

│       │   │   └── security.py
│       │   │       # Auth logic (JWT, hashing, OAuth later)

│       │   ├── models/
│       │   │   └── user.py
│       │   │       # SQLAlchemy ORM models (DB structure)
│       │   │       # Drives Alembic migrations

│       │   ├── schemas/
│       │   │   └── user.py
│       │   │       # Pydantic models (request/response validation)

│       │   ├── services/
│       │   │   └── user_service.py
│       │   │       # Business logic (NOT in routes)
│       │   │       # Example: create_user(), get_user()

│       │   └── tasks/
│       │       └── worker.py
│       │           # Celery app + async/background jobs
│       │           # Example: send_email, scrape_data

│       └── tests/
│           # Pytest tests for API, services, DB
│           # Include async tests with pytest-asyncio

├── data_pipeline/
│   ├── raw/
│   │   # Raw input data (CSV, JSON, scraped HTML)
│   │   # NEVER modify → source of truth

│   ├── processed/
│   │   # Cleaned/transformed data (after pandas, etc.)

│   ├── scrapers/
│   │   # Playwright / Selenium / requests logic
│   │   # Extract data from external sources

│   ├── loaders/
│   │   # Load processed data into DB
│   │   # Uses SQLAlchemy / async sessions

│   ├── cleaning/
│   │   # Data transformation (pandas)
│   │   # Raw → structured format

│   └── jobs/
│       # Orchestration layer
│       # Later: Dagster pipelines, schedules, sensors

├── shared/
│   ├── utils/
│   │   # Shared helpers (logging, date utils, etc.)

│   ├── schemas/
│   │   # Shared Pydantic models (used across services)

│   └── configs/
│       # Shared configuration logic (env parsing, constants)

├── data/
│   ├── snapshots/
│   │   # DB snapshots / exports (CSV, SQL dumps, parquet)
│   │   # Point-in-time data backups (NOT full DB backup system)

│   ├── exports/
│   │   # Data shared externally (reports, API exports)

│   └── tmp/
│       # Temporary files during processing

├── scripts/
│   ├── run_migrations.sh
│   │   # Runs Alembic migrations

│   ├── populate_db.sh
│   │   # Seed database with initial/test data

│   └── clear_db.sh
│       # Reset database (drop tables, clean state)

├── .devcontainer/
│   ├── devcontainer.json
│   │   # VS Code DevContainer config
│   │   # Defines service, ports, extensions

│   └── docker-compose.dev.yml
│       # Dev overrides:
│       # - mount code
│       # - override command (sleep infinity)

└── deploy/
    ├── postgres/
    │   └── init.sql
    │       # DB bootstrap ONLY (extensions, roles)
    │       # NOT for schema

    ├── prometheus/
    │   └── prometheus.yml
    │       # Metrics scraping config

    └── nginx/ (optional)
        # Reverse proxy config (production)