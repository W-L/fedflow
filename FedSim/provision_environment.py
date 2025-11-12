import argparse

from fabric import SerialGroup

from FedSim.utils import construct_client_strings, read_toml_config


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare environment for FedSim clients.")
    parser.add_argument("-c", "--conf", help="Path to TOML config file")
    parser.add_argument("-i", "--sshkey", help="Path to SSH key file", default=None)
    parser.add_argument("-p", "--provision", help="Path to provisioning script to run on remote clients", default=None)
    args = parser.parse_args()
    return args



def main(args) -> None:
    client_strings = construct_client_strings(config=args.conf)
    print(client_strings)

    # get remote username
    clients = read_toml_config(args.conf)['clients']
    remote_username = list(clients.values())[0]['username']

    if args.sshkey:
        serialg = SerialGroup(*client_strings, connect_kwargs={"key_filename": args.sshkey})
    else:
        serialg = SerialGroup(*client_strings)

    provision_script = args.provision

    for cxn in serialg:
        cxn.put(f'VMs/{provision_script}', remote=f'/home/{remote_username}/{provision_script}')
        provision = cxn.run(f'bash /home/{remote_username}/{provision_script}')
        print(provision.stdout)
        print(provision.stderr)

    serialg.close()
    

if __name__ == "__main__":
    args = get_args()
    main(args)  


