import argparse
from pathlib import Path

from fedsim.config import Config


"""
Script to provision remote machines from a shell script. E.g. if vagrant/ansible are not available
"""


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Provision remotes with a shell script")
    parser.add_argument("-c", "--conf", help="Path to fedsim TOML config file")
    parser.add_argument("-i", "--sshkey", help="Path to SSH key file to access remote")
    parser.add_argument("-p", "--provision", help="Path to provisioning script to run on remotes")
    args = parser.parse_args()
    return args



def main(args):
    # load the config of remotes
    conf = Config(toml_path=args.conf)
    # construct the fabric serial group
    serialg = conf.construct_serialgroup()
    # which script to execute on remotes
    prov = Path(args.provision)
    prov_name = prov.name
    # loop through the remotes
    for cxn in serialg:
        print(f'copying {prov_name} to {cxn["host"]}')
        remote_user = cxn['user']
        cxn.put(f'{prov}', remote=f'/home/{remote_user}/{prov_name}')
        print('running script')
        provision = cxn.run(f'bash /home/{remote_user}/{prov_name}')
        print(provision.stdout)
        print(provision.stderr)
    serialg.close()
    

if __name__ == "__main__":
    args = get_args()
    main(args)  


