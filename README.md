# fedflow

The aim of this project is to automate federated workflows with FeatureCloud.ai by orchestrating remote machines. FeatureCloud.ai enables federated machine learning through a web interface and a locally executed controller instance. However, analyses require manual interaction with the graphical interface of the website by all participating clients. This is prohibitive for iterative analyses and results in analyses that are not easily reproducible.

This package introduces i) an API to interact headlessly with FeatureCloud.ai ii) the orchestration of remote machines (e.g. VMs) to execute fully-automated federated analyses, and iii) an example of a fully reproducible snakemake workflow using this package.



## Concept

Fedflow is an orchestration tool to use FeatureCloud.ai in reproducible workflows without manual interaction. 
It is designed to either run federated analyses on locally-simulated VMs for testing purposes, or to execute the same workflow on remote machines (e.g. cloud instances or machines at participating research institutes). 


<img src="figures/fedflow_overview.png" alt="fedflow_overview" width="500"/>


<br>

---

<br>


<img src="figures/fedflow_remote.png" alt="fedflow_remote" width="500"/>



## Requirements & installation


fedflow can be installed with pip

`pip install fedflow-featurecloud`


For simulations vagrant, libvirt and the vagrant-libvirt plugin are required

  - Instructions to install vagrant: https://developer.hashicorp.com/vagrant/install

  - Installing libvirt on a debian/ubuntu-based system: `sudo apt update && sudo apt install libvirt-daemon-system`

  - Instructions for the vagrant-libvirt plugin: https://vagrant-libvirt.github.io/vagrant-libvirt/installation.html#ubuntu--debian


User accounts on FeatureCloud.ai need to be created via the website.


## Usage

There are 2 main components in this project: 

1) a program to run federated workflows via FeatureCloud.ai headlessly: `fedflow`
1) an API to interact with FeatureCloud.ai: `fcauto`. `fedflow` uses this API to execute workflows, hence users are not required interact directly with it.


### fedflow

This program orchestrates all client machines and instructs them to interact with FeatureCloud.ai to automate federated workflows.


```
usage: fedflow [-h] (-c CONFIG | -t)

Federated FeatureCloud.ai workflows on remote machines

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to the config file
  -t, --template        Generate template config
```



### fcauto

This is an API for the FeatureCloud.ai website. It's primary purpose is to be used by `fedflow`, but it can also be used in a stand-alone manner.
There are several subcommands to interact with FeatureCloud.
Check `fcauto SUBCOMMAND --help` for arguments/options.


```
usage: fcauto [-h] {create,join,monitor,query,contribute,reset,list-apps} ...

FeatureCloud automation tool

positional arguments:
  {create,join,monitor,query,contribute,reset,list-apps}
    create              Create a new FeatureCloud project (as coordinator)
    join                Join an existing FeatureCloud project
    monitor             Monitor a running FeatureCloud project
    query               Query FeatureCloud project status
    contribute          Contribute data to a FeatureCloud project
    reset               Reset a FeatureCloud project to status 'ready'
    list-apps           List available apps on FeatureCloud

options:
  -h, --help            show this help message and exit
```




## Configuration

Configuration of `fedflow` requires 2 files. 

1) An environment file that contains the credentials of the participating FeatureCloud.ai users. 


This is in the format USER=PASSWORD in `.env` in the working directory.

FeatureCloud accounts are low-privilege and low-impact if compromised, since they contain very limited information and the platform itself holds no data or results of previous analyses.
In a multi-user environment it is advised to set `chmod 600 .env && chown <user> .env`




2) A toml configuration of an automated FeatureCloud workflow. 

A template config file can be generated with `fedflow -t` The format is as follows:


```
project_id = 0
tool = ""
sim = false
outdir = "results/"

[[clients]]
fc_username = "FC_USER"
data = []
coordinator = false
username = "USER"
hostname = "HOSTNAME"
sshkey = ".ssh/id_rsa"

[[clients]]
fc_username = "FC_USER"
data = []
coordinator = false
username = "USER"
hostname = "HOSTNAME"
sshkey = ".ssh/id_rsa"

```

The config must either contain `tool=<str>` with one of the FeatureCloud apps (either listed on their website or with `fcauto list-apps`) or `project_id=<int>`. If a `tool` is given, a new project template will be created and used, if `project_id` is given a previously-created project template will be used instead.

If `sim = true` is set, vagrant VMs are launched and used for the federated execution. In that case the parameters `hostname, username, port, sshkey` of all clients are ignored.
To use other remote machines these connection details need to be provided. The field `sshkey` is the path to the ssh key used to authenticate the user on the remote. Exchange of connection credentials is only automated when using vagrant VMs.

The clients participating in the federated analysis are specified as an array of `[[clients]]`. One client is required to take the role of `coordinator = true`. This client's FeatureCloud user will create or initiate the project and monitor its execution.


## Example usage


In `example/` there are test data and configurations to run the 'mean' test app across 3 clients. FeatureCloud users need to be provided in the config `example/config_mean.toml`, and their credentials in a `.env` file.


`fedflow -c config_mean.toml`


## Provisioning of client VMs/participating machines


System dependencies on remotes are installed automatically using a shell script shipped in `fedsim/provision.py`.
 
- python3.12, python3.12-venv
- docker


## Limitations 

The API in this project does not automate the creation of user accounts for FeatureCloud.ai or the registration of their participating sites. 




## Terms of accceptable use and responsible automation

This library provides programmatic access to functionality of featurecloud.ai that is normally available through manual interaction with the website. It does not bypass authentication mechanisms or access controls.
To promote responsible use, the library enforces request limits and identifies itself explicitly via a User-Agent header at each request. These measures are intended to reduce the risk of excessive load or unintended disruption to the website.
Users are responsible for ensuring that their use of this library complies with the website’s Terms of Service and applicable policies. High-volume scraping, aggressive polling, or other usage patterns that exceed normal interactive behavior are out of scope and may result in blocking by the website operator.
If the website signals rate limiting or access restrictions (e.g. HTTP 429 or 403 responses), users need to reduce their request frequency or stop usage. The author does not operate or control the target website and makes no guarantees regarding access or compatibility.



## pytests


Run the pytest suite with `pytest -s --cov` or `pytest -s --cov -m 'not integration'` to skip slow tests. 
There are not many tests not marked as integration though, since most of the code in this project interacts with VMs.
Some tests require featurecloud credentials in the environment, which are not provided in this repo.


## Example analysis

The directory `analysis/workflow_comp` contains an example analysis workflow that runs different FeatureCloud analyses with the automation described here. Details are available in a separate `README.md`.




