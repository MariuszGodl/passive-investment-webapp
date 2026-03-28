#!/usr/bin/env bash
set -a; source .env; set +a

git config --global --add safe.directory /src
pip install pre-commit && pre-commit install