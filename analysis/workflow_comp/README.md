# fedsim_comp

This repository contains a reproducible snakemake workflow that compares the execution of centralised and federated analyses. For running the federated tools featurecloud.ai is used via fedsim (custom VM & API automation tool for featurecloud). Both kinds of analyses are run through fedsim; the centralised analysis with a single client that possesses all data and the federated analyses with several clients that only have access to a portion of the data. The client-local results are combined in this workflow after the federated steps.

At the moment the workflow compares these federated tools:

- federated-svd
- random-forest
- ada-boost





## Setup & configuration

The workflow depends on a conda environment which can be installed with:

`conda env create -f env.yaml -n comp && conda activate comp`

The workflow also needs fedsim to be installed. 
Since it is not on pypi yet, it needs to be pulled from the repo and then installed via pip. 
Once it is on pypi I'll add it to the conda dependencies.

`git clone https://github.com/W-L/FedSim.git`
`cd FedSim && hatch build && pip install .`

or to avoid another local repo, just copy the wheel and install that

`cp ../FedSim/dist/fedsim-0.0.1-py3-none-any.whl dist/`


all configurable parameters of the workflow are in 

`workflow/config/config.yaml`




## Run workflow

`conda activate comp`

`snakemake --resources serial=1 -p -cN`

`--resources serial=1` makes sure that multiple runs of fedsim are performed in series to avoid that individual fedsim runs use the same VMs concurrently.



## Steps

`snakemake --rulegraph | dot -Tpng > rulegraph.png && snakemake --dag | dot -Tpng > jobgraph.png`

<img src="figs/rulegraph.png" alt="rulegraph" width="500"/>

<img src="figs/jobgraph.png" alt="jobgraph" width="500"/>

- prep_data
    - download public cohort data
    - filter to project accessions (listed in workflow config.yaml)
    - write data files for each federated client and for centralised analysis

- fedsim_svd & fedsim_randfor
    - runs twice (forced serially), once with a single client and all data, and once with 5 clients and separated data
    - config files for the fedsim runs are in resources/

- unzip_fedsim
    - extract fedsim results for all clients 

- combine_federated_*
    - concatenate the federated output data 
    - adds a column to identify the client/project accession for visualisation

- viz_*
    - these scripts are run manually for now
    - create figures to compare centralised and federated runs



## Results


<img src="figs/viz_vagrant_federated-svd.png" alt="embedding" width="500"/>

Embedding of downsampled species signal features for a centralised analysis (A), and a federated run with 5 clients (B). The embeddings are identical for both executions. The input features were randomly downsampled to 5%, i.e. ~130 columns, to save on execution time.



<br>

---

<br>


<img src="figs/viz_vagrant_randfor.png" alt="randfor" width="700"/>

Results of random forest classification for a centralised versus federated analysis. 
The input data was downsampled to 5% of the total features, and the training and test data are equivalent. 
So these results have no meaning except for comparison of the analyses.
(A) Scatter plot of probabilities for class 1 for the centralised (x-axis) and federated analyses (y-axis).
(B) ROC curves and deltaAUC of the global versus local classifiers.
(C) Densities of probalities for class 1 separated by true class label (vertical) and by classifier (horizontal)



<br>

---

<br>



### adding new tool

- add config files in configs/ (tool and fedsim config)
- add tool name in workflow config
- add input data (adjust preparation script)
- run the tools via fedsim once outside the snakemake to generate the project IDs
- add snakemake rules (overloaded fedsim and unzipping)
- add combination script
- add visualisation script 
- add figures to readme
- update rulegraph


