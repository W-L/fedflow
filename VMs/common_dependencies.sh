# install common dependencies for FedSim VMs
# provisioning script for vms

apt update
apt install curl pip

# install docker from their convenience script
curl -fsSL https://get.docker.com -o get-docker.sh
sh ./get-docker.sh

# install python dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# install playwright browsers
playwright install firefox

