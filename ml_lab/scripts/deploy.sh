#!/bin/bash

# ML Lab Deployment Script
# This script deploys ML Lab to production

set -e

echo "🚀 Deploying ML Lab..."

# Configuration
IMAGE_NAME="ml-lab"
CONTAINER_NAME="ml-lab"
REGISTRY="${REGISTRY:-docker.io}"
TAG="${TAG:-latest}"

# Build Docker image
echo "📦 Building Docker image..."
docker build -t ${REGISTRY}/${IMAGE_NAME}:${TAG} .

# Tag for registry
echo "🏷️  Tagging image..."
docker tag ${REGISTRY}/${IMAGE_NAME}:${TAG} ${REGISTRY}/${IMAGE_NAME}:latest

# Push to registry (if registry is set)
if [ -n "${REGISTRY}" ] && [ "${REGISTRY}" != "docker.io" ]; then
    echo "📤 Pushing to registry..."
    docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}
    docker push ${REGISTRY}/${IMAGE_NAME}:latest
fi

# Stop existing container
echo "🛑 Stopping existing container..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

# Run new container
echo "▶️  Starting new container..."
docker run -d \
    --name ${CONTAINER_NAME} \
    -p 8501:8501 \
    -e DATABASE_URL="${DATABASE_URL}" \
    -e ARTIFACT_STORAGE_PATH="/app/artifacts" \
    -v $(pwd)/artifacts:/app/artifacts \
    -v $(pwd)/models:/app/models \
    -v $(pwd)/reports:/app/reports \
    --restart unless-stopped \
    ${REGISTRY}/${IMAGE_NAME}:${TAG}

echo "✅ Deployment complete!"
echo "🌐 ML Lab is available at http://localhost:8501"
