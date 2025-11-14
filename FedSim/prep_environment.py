import argparse
import os

from dotenv import load_dotenv

from utils import read_toml_config, construct_client_strings, construct_serialgroup
from fabric_utils import write_to_file_remote, transfer_with_packing, upload_file
    


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
    parser.add_argument("-i", "--sshkey", help="Path to SSH key file", default=None)
    args = parser.parse_args()
    return args





def transfer_data(conn, data: list, target_dir: str, config_file: str):
    transfer_with_packing(conn=conn, paths=data, remote_dir=target_dir)
    upload_file(conn=conn, local_path=config_file, remote_path=f"{target_dir}/config.toml", force=True)


def transfer_credentials(conn, target_dir: str, client_name: str) -> None:
    fc_user = os.getenv(client_name)
    fc_pass = os.getenv(f"{client_name}_P")
    assert fc_user is not None and fc_pass is not None, f"credentials {client_name} not found"
    write_to_file_remote(conn=conn,
                         remote_path=f"{target_dir}/.env",
                         content=f"FC_USER={fc_user}\nFC_PASS={fc_pass}\n")
    



def main(args) -> None:
    # load config and credentials
    conf = read_toml_config(args.conf)
    
    # grab some values from config
    target_dir = conf['vm']['target_dir']
    clients = conf['clients']

    # load credentials into environment
    load_dotenv(dotenv_path=args.creds, override=True)

    # construct serial group    
    serialg = construct_serialgroup(conf=args.conf, sshkey=args.sshkey)


    for (pname, pinfo), cxn in zip(clients.items(), serialg):
        transfer_credentials(conn=cxn, target_dir=target_dir, client_name=pname)
        transfer_data(conn=cxn, data=pinfo['data'], target_dir=target_dir, config_file=args.conf)

    # close connections
    serialg.close()

  
if __name__ == "__main__":
    args = get_args()
    main(args)


    



