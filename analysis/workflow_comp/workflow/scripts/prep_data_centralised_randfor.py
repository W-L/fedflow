import argparse
import pandas as pd
from pathlib import Path


# simply load and merge the separated files into a centralised one


def get_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--accs", type=str, nargs='+', required=True)
    parser.add_argument("--nreps", type=int, required=True)
    args = parser.parse_args()
    return args



args = get_args()


for n in range(args.nreps):
    print(n)
    # grab all federated files for the given rep and merge them into a centralised one    
    dfs_to_merge = []
    dfs_to_merge_test = []
    for acc in args.accs:
        data_path = Path('data') / "random-forest" / "fed" / acc / f"{n:03d}" / "input.csv"
        data_test_path = Path('data') / "random-forest" / "fed" / acc / f"{n:03d}" / "input_test.csv"
        data = pd.read_csv(data_path, sep=',')
        data_test = pd.read_csv(data_test_path, sep=',')
        dfs_to_merge.append(data)
        dfs_to_merge_test.append(data_test)

    # save to centralised file
    combo_path = Path("data") / "random-forest" / "cent" / "P0" / f"{n:03d}"
    combo_path.mkdir(parents=True, exist_ok=True)

    combo_df = pd.concat(dfs_to_merge, axis=0)
    combo_df_test = pd.concat(dfs_to_merge_test, axis=0)
    combo_df.to_csv(combo_path / "input.csv", sep=',', index=False)
    combo_df_test.to_csv(combo_path / "input_test.csv", sep=',', index=False)

 