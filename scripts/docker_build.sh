#!/bin/bash

# Set the image name (you can customize this)
IMAGE_NAME=job-posting-analyzer

# Build the Docker image
docker build -t shiyanra/$IMAGE_NAME:latest .

docker push shiyanra/$IMAGE_NAME:latest

echo "Docker image '$IMAGE_NAME' built and pushed successfully!"