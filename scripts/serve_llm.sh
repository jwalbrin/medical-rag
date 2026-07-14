#!/usr/bin/env bash
set -euo pipefail

# Load .env from project root for IMAGE and HF_MODEL only
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"
if [[ -f "$ENV_FILE" ]]; then
  set -o allexport
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +o allexport
fi

IMAGE="${LLAMACPP_IMAGE:-ghcr.io/ggml-org/llama.cpp:full-cuda}"
HF_MODEL="${LLM_MODEL:-unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL}"

HOST_PORT=$(echo "${LLM_BASE_URL:-http://localhost:8080}" | sed 's|.*:||')
HF_CACHE="$HOME/.cache/huggingface"
N_GPU_LAYERS=99
CONTEXT_SIZE=65536
N_PARALLEL=1
FLASH_ATTN=on

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "docker run --rm -d \\"
  echo "  --gpus all \\"
  echo "  -p ${HOST_PORT}:8080 \\"
  echo "  -v ${HF_CACHE}:/root/.cache/huggingface \\"
  echo "  ${IMAGE} \\"
  echo "  --server \\"
  echo "  -hf ${HF_MODEL} \\"
  echo "  --host 0.0.0.0 --port 8080 \\"
  echo "  -ngl ${N_GPU_LAYERS} -c ${CONTEXT_SIZE} -fa ${FLASH_ATTN} -np ${N_PARALLEL}"
  exit 0
fi

echo "Starting llama.cpp server on http://localhost:${HOST_PORT}"
echo "  image : ${IMAGE}"
echo "  model : ${HF_MODEL}"
echo "  cache : ${HF_CACHE}"
echo

CONTAINER_ID=$(docker run --rm -d \
  --gpus all \
  -p "${HOST_PORT}:8080" \
  -v "${HF_CACHE}:/root/.cache/huggingface" \
  "${IMAGE}" \
  --server \
  -hf "${HF_MODEL}" \
  --host 0.0.0.0 --port 8080 \
  -ngl "${N_GPU_LAYERS}" \
  -c "${CONTEXT_SIZE}" \
  -fa "${FLASH_ATTN}" \
  -np "${N_PARALLEL}")

echo "Container started: ${CONTAINER_ID}"
echo "Logs: docker logs -f ${CONTAINER_ID}"
echo "Stop: scripts/stop_llm.sh"
