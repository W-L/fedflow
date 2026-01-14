
## Notes

Notes on quirks of the featurecloud tools


### Details on SVD output files

These are my interpretations of the output files:

- eigenvalues.tsv: Eigenvalues of the global covariance matrix. Each value corresponds to a principal component (PC) and measures variance captured. These are global?
- variance_explained.csv: Eigenvalues normalized to fractions of total variance. These are global?
- right_eigenvectors.tsv: Loadings (principal axes). Columns are PCs; rows are features. These define the shared global PCA space.
- left_eigenvectors.tsv: Scores of samples in PC space up to scaling.
- projections / localData.csv: Per-client projections of samples onto the global PCs.
- scaled_data.tsv: Globally centered and scaled data used for PCA.


### input format issue for federated-svd

The instructions say that rows should be samples, and columns should be features. However, it only works when the input is transposed:

https://github.com/AnneHartebrodt/fc-federated-svd/issues/2



### config file name

for some featurecloud tools the config file name is hard coded

- random-forest: config.yml
- ada-boost: config.yml
- mean-app: config.yml

### Ada-boost

This tool does not provide predictions or probabilities as output, only the pickled model and scores on local test data. 
I'm not able to unpickle the model, maybe because I don't have the exact versions of some of the libraries. 
The requirements are not fully pinned though, so there's no easy way to reproduce the environment fully.


### Mean-app

The input for this app needs to be called 'data.csv', otherwise the tool will print a log message that the input can't be found and will keep running forever.
The output is always called 'results.txt' irrespective of what is set in the config.yml.

