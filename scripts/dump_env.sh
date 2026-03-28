#!/usr/bin/env bash

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT}/.env"

umask 077
{
  printf 'GH_TOKEN=%q\n' "${GH_TOKEN:-}"
  printf 'DATABASE_URL=%q\n' "${DATABASE_URL:-postgresql+asyncpg://postgres:postgres@db:5432/app_db}"
} >"${ENV_FILE}"
