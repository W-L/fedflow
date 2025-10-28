import os
from dotenv import load_dotenv
from pathlib import Path
import argparse

from FedSim.utils import read_toml_config


"""
a simple script to prepare the environment for computing across VMs
this is executed once and distributes data and credentials for each client
this would not be part of a real analysis, just to prep simulations

Usage:
    python prep_environment.py -c resources/config_svd.toml -e resources/.env

"""


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare environment for FedSim clients.")
    parser.add_argument("-c", "--conf", help="Path to TOML config file")
    parser.add_argument("-e", "--creds", help="Path to dotenv file containing credentials for clients")
    args = parser.parse_args()
    return args


class Client: 

    def __init__(self, name: str, target_dir: str):
        self.name = name
        self.target_dir = target_dir
        self.client_path = Path(target_dir) / name
        self.client_path.mkdir(parents=True, exist_ok=True) 


    def write_credentials(self):
        cred_file = self.client_path / ".env"
        with open(cred_file, "w") as f:
            f.write(f"{self.name}={os.getenv(self.name)}\n")
            f.write(f"{self.name}_P={os.getenv(f'{self.name}_P')}\n")


    def link_data(self, source_path: str):
        data_src = Path(source_path) 
        data_dst = self.client_path / f"{self.name}_data"
        if data_dst.exists():
            return
        else:
            os.symlink(data_src, data_dst)




def main(config_path: str, credentials_path: str):
    # load config and credentials
    conf = read_toml_config(config_path)
    load_dotenv(dotenv_path=credentials_path, override=True)

    # grab some directories
    target_dir = conf['vms']['target_dir']
    participants = conf['clients']['participants']

    for p in participants:
        # create clients
        client = Client(name=p, target_dir=target_dir)
        # distribute credentials into VM-specific .env files
        client.write_credentials()
        # link data into each client directory
        client.link_data(source_path=conf['data'][client.name])

  

if __name__ == "__main__":
    args = get_args()
    main(config_path=args.config, credentials_path=args.creds)



