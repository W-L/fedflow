import argparse

from dotenv import load_dotenv

from FedSim.utils import read_toml_config
from FedSim.remote_client import Client


"""
a simple script to prepare the environment for computing across VMs
transfers data and FC credentials to each client VM

Usage:
    python FedSim/prep_environment.py -c resources/config_svd.toml -e resources/.env
"""


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare environment for FedSim clients.")
    parser.add_argument("-c", "--conf", help="Path to TOML config file")
    parser.add_argument("-e", "--creds", help="Path to dotenv file containing credentials for clients")
    args = parser.parse_args()
    return args






def main(config_path: str, credentials_path: str):
    # load config and credentials
    conf = read_toml_config(config_path)
    load_dotenv(dotenv_path=credentials_path, override=True)

    # grab some directories
    target_dir = conf['vm']['target_dir']
    participants = conf['clients']

    for pname, pinfo in participants.items():
        # create clients
        client = Client(name=pname, info=pinfo, target_dir=target_dir)
        # write credentials to .env file in remote
        client.get_credentials()
        # transfer data to remote, and the config file as well
        client.transfer_data(target_dir=target_dir, config_file=config_path)
        

  
if __name__ == "__main__":
    args = get_args()
    conf = args.conf
    creds = args.creds
    # debug
    # conf = "resources/config_svd.toml"
    # creds = "resources/.env"


    main(config_path=conf, credentials_path=creds)
    



