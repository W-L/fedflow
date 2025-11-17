import argparse

from FedSim.utils import read_toml_config, construct_serialgroup


"""
This is not necessary if the provisioning can be done via vagrant/ansible
"""



def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare environment for FedSim clients.")
    parser.add_argument("-c", "--conf", help="Path to TOML config file")
    parser.add_argument("-i", "--sshkey", help="Path to SSH key file", default=None)
    parser.add_argument("-p", "--provision", help="Path to provisioning script to run on remote clients", default=None)
    args = parser.parse_args()
    return args



def main(args) -> None:
    # construct the fabric serial group
    serialg = construct_serialgroup(conf=args.conf, sshkey=args.sshkey)
    # grab the remote username
    clients = read_toml_config(args.conf)['clients']
    remote_username = list(clients.values())[0]['username']

    provision_script = args.provision
    provision_script_name = provision_script.split('/')[-1]

    for cxn in serialg:
        print('copying script')
        cxn.put(f'{provision_script}', remote=f'/home/{remote_username}/{provision_script_name}')
        print('running script')
        provision = cxn.run(f'bash /home/{remote_username}/{provision_script_name}')
        print(provision.stdout)
        print(provision.stderr)

    serialg.close()
    

if __name__ == "__main__":
    args = get_args()
    main(args)  


