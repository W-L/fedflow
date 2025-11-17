# FedSim

Automation of federated analyses with featurecloud.ai

Either simulated with VMs or with real machines via ssh


This project has multiple layers:
- vm/ssh infrastructure
- sending commands to machines via fabric
- a reverse engineered featurecloud API
- featurecloud tools themselves (IO)



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

Manual setup on FC GUI that are not automated:
- register accounts on FC for all clients
- create 'sites' for all clients





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


## 2 modes of operation

either simulation with vagrant : everything in a single python script and 1 config file
- even vagrantfile is abstracted away

other mode is to give details for remotes in config file
- no need to bring them up, but still need to provision (via fabric instead of vagrant file)
- or ask sysadmin of the partners to install certain things 






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


project creation and joining is now implemented
- only simple projects with a single tool so far



continue developing the fc api
- add multiuser scenarios



make sure the client is linked to the correct vm
- i.e. I think the serialgroup and clients get linked incorrectly in the clients class

test the fc workflow (IO e.g.) 

write some convenience scripts that check the log files of all machines

create other workflows for other tools

write a snakemake workflow to run all analyses and compare them to centralised approaches


in the provisioning script, the docker version is currently fixed due to FC restrictions
- check once their container is updated


create a conda env for all development dependencies (same as on the vms)
- also document that vagrant and libvirt is req


document usage and the toml config file

write type hints and function docstrings

setup file and installable with pip install .


write pytests for everything
- trickier for remote stuff, but should be ok


automate user registration and site creation?
and purchasing of apps?