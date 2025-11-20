# FedSim

The aim of this project is to automate federated analyses of featurecloud.ai either as simulation or to orchestrate real machines.

The main components are: 

- setup and provisioning of VMs using vagrant
- instructions are sent to clients via the python module fabric
- a reverse engineered featurecloud API that allows for headless interaction with featurecloud.ai


What this project does not automate:

- user creation at featurecloud.ai
- user's site registration at featurecloud.ai
- 'purchasing' apps in the featurecloud.ai app store
- featurecloud apps that require frontend interaction of the coordinator


## Configuration

Configuration of this project requires 2 components. An environment file that contains all credentials of the featurecloud.ai users. This should be in the format USER=PASSWORD and be placed in `.env` in the root of the project.

The configuration of simulations/real runs of featurecloud is done in a single toml file. The format is as follows:

```
[general]

sim = true                              # whether vagrant VMs or real machine are used
project_id = PROJECT_ID                 # numeric ID of a featurecloud project (in it's URL)
tool = TOOL_NAME                        # alternatively to a project_id, then a project is created automatically


[clients]

[clients.0]
fc_username = USERNAME
data = ["path/to/file1", "path/to/file2"]
coordinator = true
hostname = ''                           # these fields can be left empty when using vagrant
username = ''                           # if real machines are used, their details go here
port = '' 
sshkey = '' 


[clients.1]
fc_username = USERNAME
data = ["path/to/file1", "path/to/file2"]
hostname = ''
username = ''
port = '' 
sshkey = '' 

...


```


If `sim = true` is set, `hostname, username, port, sshkey` are ignored and vagrant vms are used instead. When real machines should be used, their connection details need to be provided.


## Requirements

For execution a python virtual environment with a few dependencies is needed. 
The dependencies and the project itself can be installed with pip.

```
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

For simulations vagrant and some virtualisation provider are required. (Using libvirt in development)

```
wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install vagrant
vagrant plugin install vagrant-libvirt
```



## Provisioning of client VMs/participating machines

For simulations, the VMs are provisioned automatically (`VMs/vagrant_provision.sh`). 
The script can also be used to set up other ubuntu-based participants. (not automated for now)

It installs these dependencies:

- python and the environment mentioned above
- docker (used by featurecloud)

There's also a short script specifically for biosphere VMs (which already have python and docker installed).


## Usage











# TODO

write two interface scripts
- one for the api alone
- one for fedsim itself
- i.e. have a behaviour switch in the argparser (subprogram or whatever it's called)


currently experiencing multiple issues with FC apps:
- inconsistent finishing behaviour (mean-app, random-forest)
- shutil copy error of the config file (federated-svd)


issue on the VMs: mounting of input data into the container fails
- this is prohibitive for execution at the moment
- but has nothing to do with the reverse-engineered featurecloud API


write some convenience scripts that check the log files of all machines
- including the logs of the fc controllers and the fc apps


in the provisioning script, the docker version is currently fixed due to FC restrictions
- check once their container is updated


write type hints and function docstrings

write pytests for everything


