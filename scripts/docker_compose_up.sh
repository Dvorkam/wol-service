#!/usr/bin/env bash
set -euo pipefail

echo "Starting docker compose stack (build + up)..."
docker compose up --build "$@"
