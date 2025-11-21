#!/bin/bash

set -e 

USER="vagrant"
DOCKER_VERSION="5:28.5.2-1~ubuntu.24.04~noble"


apt-get update
apt-get install -y curl pip python3.12 python3.12-venv \
                   ca-certificates curl gnupg


# Install Docker (from vagrant tutorial)
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce=$DOCKER_VERSION docker-ce-cli=$DOCKER_VERSION containerd.io docker-buildx-plugin docker-compose-plugin
usermod -aG docker $USER




