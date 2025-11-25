#!/bin/bash

set -e

# the ubuntu box on biosphere already has python (3.12) and docker installed
# the only thing we need is venv to install and run fedsim
sudo apt-get update && sudo apt-get install -y python3.12-venv



