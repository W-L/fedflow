import argparse
from glob import glob

import rtoml



def get_args(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("--hostnames", type=str, nargs='+', required=True)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    configs = glob('configs/biosphere/*/*.toml')
    print(f"nconfigs: {len(configs)}")
    print(f"nhostnames: {len(args.hostnames)}")

    for config_path in configs:
        print(config_path)
        # load config
        with open(config_path, "r") as f:
            conf = rtoml.load(f)
        # check that we have enough hostnames
        clients = conf['clients']
        assert len(clients) <= len(args.hostnames)
        # assign hostnames
        for cl, ip in zip(clients.values(), args.hostnames):
            cl['hostname'] = ip
        # write back config
        with open(config_path, "w") as f:
            rtoml.dump(conf, f)

    # write a dummy file for snakemake
    with open(args.out, "w") as f:
        f.write('done\n')
        

if __name__ == "__main__":
    main()

 