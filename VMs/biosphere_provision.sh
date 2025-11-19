#!/bin/bash

set -e
# the ubuntu box on biosphere already has python and docker installed
sudo apt-get update && sudo apt-get install -y python3.12-venv

python3 -m venv .venv && source .venv/bin/activate
pip3 install featurecloud fabric rtoml python-dotenv httpx



