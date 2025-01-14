#!/bin/bash

# Set the image name (you can customize this)
IMAGE_NAME=job-posting-analyzer

# Build the Docker image
docker build -t ghcr.io/sean-la/$IMAGE_NAME:latest .

docker push ghcr.io/sean-la/$IMAGE_NAME:latest

echo "Docker image '$IMAGE_NAME' built and pushed successfully!"