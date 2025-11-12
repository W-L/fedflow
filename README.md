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







# TODO

create a single log file that captures everything

create a function to create the serialgroup (is used multiple times)



finally get the vm from kevin

test if vagrant works on the vm

launch and provision the vms

get the ssh info from vms, generate a new toml config file in resources with that

test if all tools work on the vms (docker, fc, playwright, ...)

get rid of remotato in this project again, was only for temp testing

test the fc workflow (IO e.g.) 

write some convenience scripts that check the log files of all machines

create other workflows for other tools

write a snakemake workflow to run all analyses and compare them to centralised approaches



