#!/usr/bin/env bash
set -euo pipefail

# This script is a helper for starting the docker-compose stack.
# By default, it starts the 'wol-service-local' service, which is
# intended for local development and mounts the source code.
#
# You can pass arguments to this script to change the behavior,
# for example, to start the production-like pypi service:
# ./scripts/docker_compose_up.sh wol-service

# Default to 'wol-service-local' if no arguments are provided.
SERVICE_NAME="${1:-wol-service-local}"
shift || true # shift fails if no args, so ignore error

echo "Starting docker compose service: '${SERVICE_NAME}' (build + up)..."
docker compose up --build -d "${SERVICE_NAME}" "$@"