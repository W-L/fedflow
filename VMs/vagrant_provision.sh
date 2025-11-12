#!/bin/bash

set -e 

USER="vagrant"

# install common dependencies for FedSim VMs
apt-get update
apt-get install -y curl pip python3.12 python3.12-venv \
                   ca-certificates curl gnupg

# install python dependencies
python3 -m venv /home/$USER/.venv
source /home/$USER/.venv/bin/activate
pip install -r playwright featurecloud fabric rtoml python-dotenv
# install playwright browsers
playwright install-deps
playwright install firefox

# Install Docker (from vagrant tutorial)
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
usermod -aG docker $USER




