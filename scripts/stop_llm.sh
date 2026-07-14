#!/usr/bin/env bash
set -euo pipefail

# Load .env from project root if present
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"
if [[ -f "$ENV_FILE" ]]; then
  set -o allexport
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +o allexport
fi

IMAGE="${LLAMACPP_IMAGE:-ghcr.io/ggml-org/llama.cpp:full-cuda}"

# Find containers running the llama.cpp image
CONTAINERS=$(docker ps --filter "ancestor=${IMAGE}" --format "{{.ID}}")

if [[ -z "$CONTAINERS" ]]; then
  echo "No running llama.cpp containers found (image: ${IMAGE})"
  exit 0
fi

echo "Stopping container(s): $CONTAINERS"
docker stop $CONTAINERS
echo "Done."
