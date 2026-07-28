import argparse
from pathlib import Path
import random



def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic mean-app benchmark inputs")
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--nclients", type=int, required=True)
    parser.add_argument("--ndata", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    return parser.parse_args()



if __name__ == "__main__":
    args = get_args()    
    outdir = args.outdir
    nclients = args.nclients
    ndata = args.ndata
    seed = args.seed

    base_rng = random.Random(seed)
    for client_index in range(nclients):
        client_dir = outdir / f"client_{client_index}"
        client_rng = base_rng.randint(0, 10**9)
        client_rng = random.Random(client_rng)
        values = [f"{client_rng.uniform(0, 1):.8f}" for _ in range(ndata)]
        client_dir.mkdir(parents=True, exist_ok=True)
        (client_dir / "data.csv").write_text(",".join(values) + "\n", encoding="utf-8")



