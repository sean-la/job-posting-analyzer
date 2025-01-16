#!/bin/bash

# Set the image name (you can customize this)
IMAGE_NAME=job-posting-analyzer

# Build the Docker image
docker build -t $IMAGE_NAME:dev .

echo "Docker image '$IMAGE_NAME' built and pushed successfully!"