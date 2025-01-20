#!/bin/bash

# Get command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      CONFIG="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Check if required arguments are provided
if [[ -z "$CONFIG" ]]; then
  echo "Error: --data argument is required"
  exit 1
fi

# Get the absolute path of the file
ABS_PATH=$(readlink -f "$CONFIG")

# Extract the directory part from the path
DIR="${ABS_PATH%/*}"
FILENAME=$(basename $CONFIG)

# Build the docker run command
docker run \
  -v "$DIR":/app/data\
  -v /var/tmp/jobs:/var/tmp/jobs\
  -v $HOME/.config/gcloud:/root/.config/gcloud \
  -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
  -e GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json \
  -e GOOGLE_CLOUD_PROJECT="$GOOGLE_CLOUD_PROJECT" \
  job-posting-analyzer:dev \
  --config /app/data/$FILENAME
  --loglevel DEBUG \
  --ignore_job_id
