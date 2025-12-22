# fedsim_comp



## Setup & configuration

`conda env create -f env.yaml -n comp && conda activate comp`

all configurable parameters are in `workflow/config/config.yaml`


pull and install fedsim (not on pypi yet)
`cd workflow && git clone https://github.com/W-L/FedSim.git`
`cd FedSim && hatch build && pip install .`

copy the wheel for fedsim
`cp -r workflow/FedSim/dist .`


## Run workflow

`snakemake --resources serial=1 --sdm conda -p -cN`

`--resources serial=1` makes sure that multiple runs of fedsim are performed in series to avoid concurrent use of the same VMs.


## Steps




### PCA output files

eigenvalues.tsv
Eigenvalues of the global covariance matrix. Each value corresponds to a principal component (PC) and measures variance captured.

variance_explained.csv
Eigenvalues normalized to fractions or percentages of total variance (often cumulative as well).

right_eigenvectors.tsv
Loadings (principal axes). Columns are PCs; rows are features. These define the shared global PCA space.

left_eigenvectors.tsv
Scores of samples in PC space up to scaling. In federated settings this is often conceptual or partial, since samples are distributed.

projections / localData.csv
Per-client projections of that client’s samples onto the global PCs (i.e., sample scores). These are what you would concatenate across clients.

scaled_data.tsv
Globally centered (and possibly scaled) data representation used for PCA. In practice this is typically reconstructed or approximated, not raw pooled data.


### combine across clients

Eigenvalues / variance explained: already global?

Right eigenvectors (loadings): already global?

Projections (scores): concatenate row-wise across clients to obtain full sample scores.

Left eigenvectors: rarely needed directly; if used, they correspond to the same PCs and align with the projections.






## Results



## Todo

`snakemake --rulegraph | dot -Tpng > figs/rulegraph.png`