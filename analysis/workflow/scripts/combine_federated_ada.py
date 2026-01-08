import pandas as pd
import argparse

parser = argparse.ArgumentParser(description="Combine federated results")
parser.add_argument("--input", type=str, help="Input files", nargs='+')
parser.add_argument("--accessions", type=str, help="project accessions", nargs='+')
parser.add_argument("--output", type=str, help="Output file")
args = parser.parse_args()

# load the results from all clients and save a combined file
all_files = args.input
accs = args.accessions

# combine and add a client identifier
dfs = []
for ada, acc in zip(all_files, accs):
    df = pd.read_csv(ada, sep="\t")
    df['client'] = acc
    dfs.append(df)

combined = pd.concat(dfs, ignore_index=True)
combined.to_csv(args.output, index=False)


