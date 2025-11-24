#!/usr/bin/env bash
set -euo pipefail

# Run the test suite using uv and the existing .venv
UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"
uv run --no-sync pytest "$@"
