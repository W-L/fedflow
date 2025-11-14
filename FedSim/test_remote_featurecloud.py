import argparse

from utils import construct_serialgroup

from fabric_utils import launch_featurecloud, stop_featurecloud




def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-c", "--conf", help="Path to TOML config file")
    parser.add_argument("-i", "--sshkey", help="Path to SSH key file", default=None)
    args = parser.parse_args()
    return args



def main(args) -> None:
    serialg = construct_serialgroup(conf=args.conf, sshkey=args.sshkey)

    for cxn in serialg:
        launch_featurecloud(conn=cxn)
        stop_featurecloud(conn=cxn)    

    serialg.close()
    

if __name__ == "__main__":
    args = get_args()
    main(args)  


