import argparse
import pandas as pd
from pathlib import Path


# simply load and merge the separated files into a centralised one


def get_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--accs", type=str, nargs='+', required=True)
    parser.add_argument("--tool", type=str, required=True)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    combo_path = Path('data') / args.tool / Path("cent")
    combo_path.mkdir(parents=True, exist_ok=True)
    combo_path /= "input.csv"

    dfs_to_merge = []
    for acc in args.accs:
        data_path = Path('data') / args.tool / acc / "input.csv"
        data = pd.read_csv(data_path, sep=',')
        dfs_to_merge.append(data)

    if args.tool == "federated-svd":
        # concatenate, but skip the id columns except for the first
        key = "msp_id"
        combo_df = pd.concat(
            [dfs_to_merge[0]] + [df.drop(columns=key) for df in dfs_to_merge[1:]],
            axis=1
        )

    elif args.tool == "random-forest":
        combo_df = pd.concat(dfs_to_merge, axis=0)
    else:
        raise NotImplementedError(f"Tool {args.tool} not implemented for centralised data prep")
    
    combo_df.to_csv(combo_path, sep=',', index=False)
    print(combo_df.shape)


if __name__ == "__main__":
    main()

 