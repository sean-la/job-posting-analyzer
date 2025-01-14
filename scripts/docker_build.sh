#!/bin/bash

# Set the image name (you can customize this)
IMAGE_NAME=job-posting-analyzer

# Build the Docker image
docker build -t "$IMAGE_NAME" .

# Optionally, tag the image (for pushing to a registry)
# docker tag $IMAGE_NAME <registry>/<username>/<image_name>:<tag>

echo "Docker image '$IMAGE_NAME' built successfully!"