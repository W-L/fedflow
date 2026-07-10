import argparse
import pandas as pd
from pathlib import Path


# simply load and merge the separated files into a centralised one


def get_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--accs", type=str, nargs='+', required=True)
    args = parser.parse_args()
    return args



args = get_args()


dfs_to_merge = []
for acc in args.accs:
    data_path = Path('data') / "federated-svd" / "fed" / acc / "000" / "input.csv"
    data = pd.read_csv(data_path, sep=',')
    dfs_to_merge.append(data)

# concatenate, but skip the id columns except for the first
key = "msp_id"
combo_df = pd.concat(
    [dfs_to_merge[0]] + [df.drop(columns=key) for df in dfs_to_merge[1:]],
    axis=1
)


combo_path = Path('data') / "federated-svd" / Path("cent") / "P0" / "000"
combo_path.mkdir(parents=True, exist_ok=True)
combo_df.to_csv(combo_path / "input.csv", sep=',', index=False)


 