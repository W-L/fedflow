# FedSim
simulated federated analyses with VMs

This project has 3 main layers:

- federated vm infrastructure
- using playwright to launch featurecloud
- featurecloud tools themselves (IO)


need to remember that the vms need to be separated as much as possible to be realistic
- there should not be any link between them





config is done in 2 ways

- credentials are in dotfiles per vm and loaded with os.getenv (because the controller does not have the other user's credentials)
- project specifications, clients, data etc. is in a toml file


## provisioning

installation:

- docker
- python
- pip 
- featurecloud CLI
- playwright
- dask

scripts: 

- initialise dask scheduler and workers on the vms
- initialise the fc controller on each vm
- on the controller, run a python script that registers as Client and orchestrates the tasks across the vms

## Setup

Manual setup on FC GUI:

- register accounts on FC for all clients
- create sites for all clients
- controller creates a project and tools within project (the number from the project URL is persistent and goes into the toml file)
- controller generates tokens and clients use tokens to join projects


for key-based ssh into VMs (check if this is actually necessary with vagrant VMS)
maybe not, but for real deployment it well be
`ssh-keygen -t rsa`
`cp ~/.ssh/KEY.pub VMs/C0/ssh/authorized_keys VMs/C1/ssh/authorized_keys ...`


Launching VMs
`vagrant`

Distribute data and credentials for all clients
`python prep_environment.py -c resources/config_svd.toml -e resources/.env`




The rest should be all automated, except if there are tools that need manual intervention in the FC GUI



## Usage

in the end this should be a single python script 
`python fedsim.py ...`



## biosphere

also possible to use biosphere instead of local vms
- they can be deployed via web interface


## devoopy02


TODO: create env file for this

conda create -n fedsim
conda activate fedsim
conda install python==3.12 fabric rtoml python-dotenv






# TODO

step through a multiuser scenario with two laptops
- this will make it clear how the running and the downloading actually works
- there is a project already with 2 users assigned
- prepping data for them in the test_data/svd_duo dir




after that create a subclass of the fcc or something to demarcate the coordinator
- then only that class can
        start
        monitor?
        download?
- all users can 
        upload



create a single log file that captures everything



continue developing the fc api
- add multiuser scenarios
- add project creation and adding other users
- add site registration


test the fc workflow (IO e.g.) 

write some convenience scripts that check the log files of all machines

create other workflows for other tools

write a snakemake workflow to run all analyses and compare them to centralised approaches


in the provisioning script, the docker version is currently fixed due to FC restrictions
- check once their container is updated

get static ips from vagrant for the hostname, should be possible right?

create a conda env for all development dependencies (same as on the vms)
- playwright needs to be installed via pip it seems, then also run playwright install firefox
