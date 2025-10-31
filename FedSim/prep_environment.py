import os
from pathlib import Path
import argparse

from dotenv import load_dotenv
from fabric import Connection

from FedSim.utils import transfer_with_packing, write_to_file_remote, test_fabric_connection, read_toml_config


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



class Client: 

    def __init__(self, name: str, info: dict, target_dir: str):
        self.name = name
        self.info = info
        self.target_dir = Path(target_dir)
        self.conn = Connection(f"{info['username']}@{info['hostname']}:{info['port']}")
        # verify that connection works and that we get expected returns
        test_fabric_connection(conn=self.conn, hostname=info['hostname'], username=info['username'])

    

    def get_credentials(self):
        self.fc_user = os.getenv(self.name)
        self.fc_pass = os.getenv(f"{self.name}_P")
        write_to_file_remote(conn=self.conn,
                                          remote_path=str(self.target_dir / ".env"),
                                          content=f"FC_USER={self.fc_user}\nFC_PASS={self.fc_pass}\n")
        



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
        # transfer data to remote
        transfer_with_packing(conn=client.conn, paths=pinfo['data'], remote_dir=target_dir)
        

  
if __name__ == "__main__":
    args = get_args()
    main(config_path=args.conf, credentials_path=args.creds)
    # debug
    # config_path = "resources/config_svd.toml"
    # credentials_path = "resources/.env"




