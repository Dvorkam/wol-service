#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${IMAGE_TAG:-wol-service:local}"

echo "Building image ${IMAGE_TAG}..."
docker build -t "${IMAGE_TAG}" .
echo "Done. Run with:"
echo "  docker run -p 25644:25644 \\"
echo "    -e SECRET_KEY=change-me -e ADMIN_USERNAME=admin -e ADMIN_PASSWORD=adminpass \\"
echo "    -e WOL_HOSTS_PATH=/data/hosts.json -e USERS_PATH=/data/users.json \\"
echo "    -v \"\$(pwd)/data:/data\" \\"
echo "    ${IMAGE_TAG}"
