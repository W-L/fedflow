import glob
import pandas as pd
import argparse

parser = argparse.ArgumentParser(description="Combine federated results")
parser.add_argument("--input", type=str, help="Input files", nargs='+')
parser.add_argument("--accessions", type=str, help="project accessions", nargs='+')
parser.add_argument("--output", type=str, help="Output file")
args = parser.parse_args()

# load the results from all clients and save a combined file
# all_files = glob.glob("results/fedsim_fed/federated.client*/17305/pca/localData.csv")
# print(all_files)
all_files = args.input
accs = args.accessions

# combine and add a client identifier
dfs = []
for fl, acc in zip(all_files, accs):
    df = pd.read_csv(fl, sep="\t")
    # name first column "sample"
    df = df.rename(columns={df.columns[0]: "sample"})
    # extract client identifier from file path and add accession
    df['client'] = f'{fl.split('/')[2]} - {acc}'  
    dfs.append(df)
combined = pd.concat(dfs, ignore_index=True)
combined.to_csv(args.output, index=False)


