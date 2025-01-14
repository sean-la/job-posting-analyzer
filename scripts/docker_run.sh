#!/bin/bash

# Get command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
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
if [[ -z "$MODE" ]]; then
  echo "Error: --mode argument is required"
  exit 1
fi

# Build the docker run command
docker run \
  -v "$DATA":/app/data\
  job-posting-analyzer \
  --config "./data/config.json" \
  --resume "./data/resume.pdf"
