import argparse

from dotenv import load_dotenv

from FedSim.utils import read_toml_config
from FedSim.featurecloud_user import Coordinator 

"""
to start the workflow as the coordinator
RUNS ON THE VM OF THE COORDINATOR

Usage:
    python FedSim/start_workflow.py --conf resources/config_svd.toml --creds resources/.env

"""


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare environment for FedSim clients.")
    parser.add_argument("-c", "--conf", help="Path to TOML config file", default="~/config.toml")
    parser.add_argument("-e", "--creds", help="Path to dotenv file containing credentials for clients", default="~/data/.env")
    parser.add_argument("-p", "--participant", help="Does the coordinator participate?", action='store_false', default=True)
    args = parser.parse_args()
    return args




def main(config_path, credentials_path):
    # load config and credentials
    conf = read_toml_config(config_path)
    load_dotenv(dotenv_path=credentials_path, override=True)


    user = Coordinator(username=conf['clients']['coordinator'])

    user.start_browser()

    user.fc_login()

    user.verify_controller_running()

    # let the coordinator start the workflow
    # user.start_workflow(proj_id=conf['project']['pid'])

    # upload data for each user
    # if args.participant:
        # user.upload_data(proj_id=conf['project']['pid'], file_path=conf['clients']['coordinator']['data'][0])


    user.stop_browser()



  
if __name__ == "__main__":
    args = get_args()
    main(config_path=args.conf, credentials_path=args.creds)
    # debug
    # config_path = "resources/config_svd.toml"
    # credentials_path = "resources/.env"


