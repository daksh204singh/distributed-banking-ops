#!/usr/bin/env bash

set -euo pipefail

TAG="${1:-latest}"
REGISTRY_NAMESPACE="${2:-}"

if [[ -n "${REGISTRY_NAMESPACE}" && "${REGISTRY_NAMESPACE}" != */ ]]; then
  REGISTRY_NAMESPACE="${REGISTRY_NAMESPACE}/"
fi

echo "Building account-service image with tag '${TAG}'..."
docker build \
  --file account-service/Dockerfile \
  --tag "${REGISTRY_NAMESPACE}account-service:${TAG}" \
  .

echo "Building transaction-service image with tag '${TAG}'..."
docker build \
  --file transaction-service/Dockerfile \
  --tag "${REGISTRY_NAMESPACE}transaction-service:${TAG}" \
  .

echo "Images built successfully."
