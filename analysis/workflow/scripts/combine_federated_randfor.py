import pandas as pd
import argparse

parser = argparse.ArgumentParser(description="Combine federated results")
parser.add_argument("--input_pred", type=str, help="Input files", nargs='+')
parser.add_argument("--input_prob", type=str, help="Input files", nargs='+')
parser.add_argument("--input_true", type=str, help="Input files", nargs='+')
parser.add_argument("--accessions", type=str, help="project accessions", nargs='+')
parser.add_argument("--output", type=str, help="Output file")
args = parser.parse_args()

# load the results from all clients and save a combined file
all_files_pred = args.input_pred
all_files_prob = args.input_prob
all_files_true = args.input_true
accs = args.accessions

# combine and add a client identifier
dfs = []
for fl_pred, fl_prob, fl_true, acc in zip(all_files_pred, all_files_prob, all_files_true, accs):
    df_pred = pd.read_csv(fl_pred, sep="\t")
    df_prob = pd.read_csv(fl_prob, sep=",")
    df_true = pd.read_csv(fl_true, sep="\t")
    # join the dataframes by simply concatenating columns (they have the same row order)
    df = pd.concat([df_true, df_prob, df_pred], axis=1)
    # extract client identifier from file path and add accession
    # df['client'] = f'{fl_pred.split('/')[2]} - {acc}'  
    df['client'] = acc 
    dfs.append(df)
combined = pd.concat(dfs, ignore_index=True)
combined.to_csv(args.output, index=False)


