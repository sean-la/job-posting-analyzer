#!/bin/bash

# Get command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --data)
      DATA="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check if required arguments are provided
if [[ -z "$DATA" ]]; then
  echo "Error: --data argument is required"
  exit 1
fi

# Build the docker run command
docker run \
  -v "$DATA":/app/data\
  -v /var/tmp/jobs:/var/tmp/jobs\
  -v $HOME/.config/gcloud:/root/.config/gcloud \
  -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
  -e GOOGLE_CLOUD_PROJECT="$GOOGLE_CLOUD_PROJECT" \
  -e SENDER_PASSWORD="$SENDER_PASSWORD" \
  ghcr.io/sean-la/job-posting-analyzer:latest \
  --config "./data/config.json" \
  --resume "./data/resume.pdf"
