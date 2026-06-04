#!/bin/bash
set -e 

username=$1
token_file=$2

# login to the cosybio gitlab
docker login gitlab.cosy.bio:5050 \
    --username "$username" \
    --password-stdin < "$token_file"


# clone the client deployment repo
if [ -d "FedDB-Client-Deployment" ]; then
    echo "Directory FedDB-Client-Deployment already exists. Skipping git clone."
else
    git clone https://github.com/fedDBNet/FedDB-Client-Deployment.git
fi


# inject the token into the compose file
compose_file="FedDB-Client-Deployment/FLNet_client/docker-compose.yml"
if ! grep -Fq "ORCH_DOCKER__GITLAB__REGISTRY_PASSWORD" "$compose_file"; then
    sed -i "/CONTAINER_FILE_TRANSFER_VOLUME_PATH=\/mnt\/input/a\      - ORCH_DOCKER__GITLAB__REGISTRY_PASSWORD=$(cat $token_file)" "$compose_file"
fi


# run the client install script  
if [ -f "FedDB-Client-Deployment/FLNet_client/env/dataimport-secrets.env" ]; then
    echo "File dataimport-secrets.env already exists. Skipping client installer."
else
    cd FedDB-Client-Deployment && python3 client_installer.py <<EOF
1
2 
n
localhost
8080

EOF
fi


# bring up the services
cd ~/FedDB-Client-Deployment/FLNet_client && docker compose up -d --wait


