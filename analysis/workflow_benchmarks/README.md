# fedflow benchmark

This directory contains a reproducible snakemake workflow to measure the scaling behaviour of the fedflow orchestrator.
The current workflow uses the FeatureCloud `mean-app` so application-side runtime stays small compared to orchestration overhead.
The workflow is designed to be run across biosphere VMs with a variable number of clients and a variable size of the input data. 


## Setup & configuration

The workflow depends on a conda environment:

`conda env create -f env.yaml -n benchmark && conda activate benchmark`

The workflow also needs the newest version of fedflow. 

`pip install fedflow-featurecloud`

All configurable parameters of the workflow (number of clients, data size, number of repeats) are in

`workflow/config/config.yaml`

The benchmark matrix is controlled through:


## Run workflow

`conda activate benchmark`

To launch many VMs on biosphere I have written a simple API call wrapper. 
Go to biosphere, launch 1 VM, copy cURL of the API call into `workflow/scripts/automation_helpers/launch_vms.sh` and change the number of required VMs.
 
`bash workflow/scripts/automation_helpers/launch_vms.sh`

Wait for all VMs to be in the RUNNING state and for them to have IP addresses assigned.

Then copy the json response of the periodic API call and run this:

`echo '<json>' | python workflow/scripts/automation_helpers/get_hostnames.py > workflow/config/hostnames.txt`

This parses all IP addresses of the VMs into a file, which is then used by the workflow to assign the correct VMs to fedflow executions.

Then it's time to run the workflow

`snakemake -n / -c`

Fedflow is actually executed with a wrapper script: `workflow/scripts/run_fedflow_with_hostlocks.py`.
This script assigns VMs to each fedflow run. This means that multiple fedflows can be run at the same time without using the same VMs. 
It also means that the number of running VMs will be used more efficiently, since only a few executions will use all of the running VMs.


For each `(nclient, data_size, repeat)` condition the workflow will:

1. random floats to be used in the featurecloud `mean-app` 
2. reserve VMs by placing a lock on them
2. generate a fedflow config using the data and reserved VMs
3. run fedflow and collect `fedflow_metrics.json`, which contains info on resource usage and timings




## Steps

`snakemake --rulegraph | dot -Tpng > rulegraph.png && snakemake --dag | dot -Tpng > jobgraph.png`

<img src="rulegraph.png" alt="rulegraph" width="300"/>


Very wide jobgraph:

<img src="jobgraph.png" alt="jobgraph" width="500"/>



## Results

Each fedflow run writes a json file of orchestration metrics alongside the regular results:

`results/nclients_<n>/size_<s>/rep_<r>/fedflow_metrics.json`

The scripts `metrics/agg_metrics.py` and `metrics/viz_metrics.R` are used to create the supplementary figure `metrics/metrics_summary.png`.






