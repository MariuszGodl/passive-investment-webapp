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
├── .gitignore
├── .pre-commit-config.yaml
├── CHANGELOG.md
├── docker-compose.yml
├── Makefile
│
├── services/
│   └── api/
│       ├── Dockerfile
│       ├── pyproject.toml
│       ├── alembic.ini
│       ├── alembic/
│       ├── app/
│       │   ├── main.py
│       │   ├── api/
│       │   │   └── v1/
│       │   │       └── router.py
│       │   ├── core/
│       │   │   ├── config.py
│       │   │   ├── db.py
│       │   │   └── security.py
│       │   ├── models/
│       │   │   └── user.py
│       │   ├── schemas/
│       │   │   └── user.py
│       │   ├── services/
│       │   │   └── user_service.py
│       │   └── tasks/
│       │       └── worker.py
│       └── tests/
│
├── shared/
│   ├── utils/
│   ├── schemas/
│   └── configs/
│
├── scripts/
│   ├── run_migrations.sh
│   ├── populate_db.sh
│   └── clear_db.sh
│
├── .devcontainer/
│   ├── devcontainer.json
│   └── docker-compose.dev.yml
│
└── deploy/
    ├── postgres/
    │   └── init.sql
    └── prometheus/
        └── prometheus.yml