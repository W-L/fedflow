

bash_provision_ubuntu = """
#!/bin/bash
set -e 


DEPS_PY="python3.12 python3-pip python3.12-venv"

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
    DOCKER_VERSION="5:28.5.2-1~ubuntu.24.04~noble"
    # Install Docker (from vagrant tutorial)
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    # sudo apt-get install -y docker-ce=$DOCKER_VERSION docker-ce-cli=$DOCKER_VERSION docker-ce-rootless-extras=$DOCKER_VERSION containerd.io docker-buildx-plugin docker-compose-plugin
    sudo apt-get install -y docker-ce docker-ce-cli docker-ce-rootless-extras containerd.io docker-buildx-plugin docker-compose-plugin 
    sudo usermod -aG docker "$SUDO_USER"
fi

"""



bash_provision_flnet = """
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

# docker run hello-world
"""


def write_provision_script(script: str) -> str:
    """
    Write the provision script to a file.
    :return: path to the provision script
    """
    script_name = "provision.sh"
    if script == 'fedflow':
        script_content = bash_provision_ubuntu
    elif script == 'flnet':
        script_content = bash_provision_flnet
    else:
        raise ValueError(f"Unknown provision script: {script}")
    
    with open(script_name, "w") as prov:
        prov.write(script_content)
        prov.write("\n")
    return script_name
    
    
