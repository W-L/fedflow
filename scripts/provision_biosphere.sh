#!/bin/bash

set -e

# the ubuntu box on biosphere already has python and docker installed
# the only thing we need is venv
sudo apt-get update && sudo apt-get install -y python3.12-venv



