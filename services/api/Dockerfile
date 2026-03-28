FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

ENV PIP_BREAK_SYSTEM_PACKAGES=1

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN python3.12 -m pip install --no-cache-dir poetry \
 && poetry config virtualenvs.create false \
 && poetry install --no-root

COPY . .
