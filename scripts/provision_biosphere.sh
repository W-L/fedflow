#!/bin/bash

set -e

# the ubuntu box on biosphere already has python (3.12) and docker (28.0.1) installed
# if the biosphere box updates docker it might stop working
# the only thing we need is venv to install and run fedsim
sudo apt-get update && sudo apt-get install -y python3.12-venv



