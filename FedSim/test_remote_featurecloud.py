import argparse

from fabric import SerialGroup

from FedSim.utils import construct_client_strings, read_toml_config

from FedSim.fabric_utils import launch_featurecloud, stop_featurecloud


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-c", "--conf", help="Path to TOML config file")
    parser.add_argument("-i", "--sshkey", help="Path to SSH key file", default=None)
    args = parser.parse_args()
    return args



def main(args) -> None:
    client_strings = construct_client_strings(config=args.conf)
    print(client_strings)

    if args.sshkey:
        serialg = SerialGroup(*client_strings, connect_kwargs={"key_filename": args.sshkey})
    else:
        serialg = SerialGroup(*client_strings)


    for cxn in serialg:
        launch_featurecloud(conn=cxn)
        stop_featurecloud(conn=cxn)    

    serialg.close()
    

if __name__ == "__main__":
    args = get_args()
    main(args)  


