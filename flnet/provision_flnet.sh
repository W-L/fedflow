#!/bin/bash
set -e 

# Provisioning script for FLNet client deployment on biosphere VMs
# Required: python3, docker, docker compose
# all already installed on biosphere VMs


DEPS_PY="python3 python3-pip python3-venv"

if dpkg -s $DEPS_PY >/dev/null 2>&1; then
    echo "Python dependencies are installed"
else
    sudo apt-get update
    sudo apt-get install -y $DEPS_PY
fi


if dpkg -s docker-ce >/dev/null 2>&1; then
    echo "Docker is installed"
else
    DEPS="curl ca-certificates gnupg"
    sudo apt-get update
    sudo apt-get install -y $DEPS

    # Install Docker (with convenience script from docker website)
    REMOVE_DEPS="docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc docker-buildx docker-buildx-plugin"
    sudo apt remove -y $(dpkg --get-selections $REMOVE_DEPS | cut -f1)
    curl -fsSL https://get.docker.com/ -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker "$USER"
    newgrp docker
fi

docker run hello-world



