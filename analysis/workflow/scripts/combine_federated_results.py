# load the results from all clients and save a combined file
#%%
import glob
import pandas as pd

all_files = glob.glob("results/fedsim_fed/federated.client*/17305/pca/localData.csv")
print(all_files)
#%%

# combine and add a client identifier
dfs = []
for f in all_files:
    df = pd.read_csv(f, sep="\t")
    # name first column "sample"
    df = df.rename(columns={df.columns[0]: "sample"})
    df['client'] = f.split('/')[2]  # extract client identifier from file path
    dfs.append(df)
combined = pd.concat(dfs, ignore_index=True)
combined.to_csv("results/fedsim_fed/combined_localData.csv", index=False)


