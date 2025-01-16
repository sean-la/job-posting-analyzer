#!/bin/bash

set -e

echo "Initializing Terraforn..."
terraform -chdir="./terraform" init \
    -backend-config="bucket=${TF_STATE_BUCKET}" 
echo "Initialization done."

echo "Planning Terraform changes..."
terraform -chdir="./terraform" plan
echo "Planning done."