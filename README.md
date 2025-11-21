# FedSim

The aim of this project is to automate federated analyses of FeatureCloud.ai either as simulations or to orchestrate real machines.

The main components are: 

- setup and provisioning of VMs using vagrant
- instructions are sent to clients via the python module fabric
- a reverse engineered featurecloud API that allows for headless interaction with featurecloud.ai


What this project does not automate:

- user creation at featurecloud.ai
- user's site registration at featurecloud.ai
- 'purchasing' apps in the featurecloud.ai app store
- featurecloud apps that require frontend interaction of the coordinator


## Requirements

Clone the project and install it.

```
git clone X && cd FedSim/
pip install .
```

For simulations vagrant and some virtualisation provider needs to be installed on the system. For development I'm using libvirt and the vagrant-libvirt plugin



## Usage

There are 2 main executables in this project: 

1) a program to interact with FeatureCloud.ai headlessly. This is called `fcauto`. 
2) a program to run simulations/real analyses headlessly. This is called `fedsim` and uses the first component internally.


### fcauto

This is based on a reverse-engineered API for the FeatureCloud.ai website. 
There are several subcommands to interact with FeatureCloud projects.
Check `fcauto SUBCOMMAND --help` for arguments/options.


```
usage: fcauto [-h] {create,join,monitor,contribute,reset} ...

FeatureCloud automation tool

positional arguments:
  {create,join,monitor,contribute,reset}
    create              Create a new FeatureCloud project (as coordinator)
    join                Join an existing FeatureCloud project
    monitor             Monitor a running FeatureCloud project
    contribute          Contribute data to a FeatureCloud project
    reset               Reset a FeatureCloud project to status 'ready'

options:
  -h, --help            show this help message and exit
```




### fedsim

This program orchestrates the participants/client machines and instructs them to interact with the FeatureCloud.ai website.

```
usage: fedsim [-h] -c CONFIG [-v]

Simulated federated analyses with VMs

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to the config file
  -v, --verbose         Enable verbose logging
```



## Configuration

Configuration of this project requires 2 files. 
An environment file that contains all credentials of the featurecloud.ai users.
This needs to be in the format USER=PASSWORD and be placed in `.env` in the root of the project.


The second file is a toml configuration of simulations/real runs of featurecloud. The format is as follows:


```
[general]

sim = true                              # whether vagrant VMs or real machine are used
project_id = PROJECT_ID                 # numeric ID of a featurecloud project (in it's URL)
tool = TOOL_NAME                        # alternatively to a project_id, then a project is created automatically


[clients]                               # a list of the participating clients

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




## Provisioning of client VMs/participating machines

For simulations, the VMs are provisioned automatically (`VMs/vagrant_provision.sh`). 
The script can also be used to set up other ubuntu-based participants. (not automated for now)

It installs these dependencies:

- python and a venv to run the programs
- the featurecloud controller
- docker (used by featurecloud)

There's also a shorter script specifically for biosphere VMs (which already have python and docker installed).






## TODO


go over readme and adjust how provisioning works

check the python version in the biosphere machines, adjust the version for venv in the provisioning script
or check if venv is already available, then we don't need any provisioning at all
apart from installing our own package

stop project and reset if timeout in monitor is reached
- set timeout very low for testing

think about a switch for reinstallation of fedsim on the vms
- and a no-deps as well



describe the usage of the 2 entry poin scripts



currently experiencing multiple issues with FC apps:
- inconsistent finishing behaviour (mean-app, random-forest)
- shutil copy error of the config file (federated-svd)


issue on the VMs: mounting of input data into the container fails
- this is prohibitive for execution at the moment
- but has nothing to do with the reverse-engineered featurecloud API


### long-term

write some convenience scripts that check the log files of all machines
- including the logs of the fc controllers and the fc apps


in the provisioning script, the docker version is currently fixed due to FC restrictions
- check once their container is updated

write pytests for everything


