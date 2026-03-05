import numpy as np
import pandas as pd 
import glob


svd_cent = glob.glob("../results/biosphere/federated-svd/cent/*/pca/localData.csv")[0]
svd_fed = "../results/biosphere/federated-svd/fed/combined_svd.csv"

# read both data frames
df_cent = pd.read_csv(svd_cent, sep="\t")
df_fed = pd.read_csv(svd_fed)

df_fed["1"] = -df_fed["1"]

cent = df_cent[["0", "1"]]
fed = df_fed[["0", "1"]]

# absolute distances between the two data frames
dist = np.linalg.norm(cent[["0","1"]].values - fed[["0","1"]].values, axis=1)

# mean and std of the distances
mean_dist = np.mean(dist)
std_dist = np.std(dist)

print(f"{mean_dist} {std_dist}")

