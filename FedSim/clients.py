from glob import glob
import json

from fabric import Connection

from utils import execute_fabric
from fabric_utils import transfer_with_packing, upload_file, write_to_file_remote
from logger import log



class Clients:

    """
    A wrapper around fabric.SerialGroup to manage client connections.
    """

    def __init__(self, serialgroup, clients):
        self.participants = []
        self.coordinator = []
        
        for cxn, (cname, cinfo) in zip(serialgroup, clients.items()):
            if cinfo.get('coordinator', False) is True:
                cxn['coordinator'] = True
                cxn['fc_username'] = cinfo.get('fc_username', '')
                cxn['data'] = cinfo.get('data', [])
                self.coordinator.append(cxn)
            else:
                cxn['coordinator'] = False
                cxn['fc_username'] = cinfo.get('fc_username', '')
                cxn['data'] = cinfo.get('data', [])
                self.participants.append(cxn)
        # list of all nodes
        self.all = self.coordinator + self.participants

        

    @staticmethod
    def ping(nodes: list) -> None:
        for cxn in nodes:
            try:
               cmd = 'echo "Ping from $(hostname)"'
               _ = execute_fabric(cmd, cxn)
            except Exception as e:
                log(f"Error during ping of {cxn.host}: {e}")
        return


    @staticmethod
    def distribute_data(nodes) -> None:
        for cxn in nodes:
            # data from the config file
            transfer_with_packing(conn=cxn, paths=cxn['data'])
            # upload code to run on nodes
            src = glob("FedSim/*.py")
            for file in src:
                upload_file(
                    conn=cxn,
                    local_path=file,
                    remote_path=f"{file}",
                    force=True
                )


    @staticmethod
    def distribute_credentials(nodes, fc_creds) -> None:
        for cxn in nodes:
            fc_user = cxn['fc_username']
            fc_pass = fc_creds.get(fc_user, '')
            write_to_file_remote(
                conn=cxn,
                remote_path=f".env",
                content=f"{fc_user}={fc_pass}\n"
            )


    @staticmethod
    def test_featurecloud_controllers(nodes) -> None:
        for cxn in nodes:
            launch_featurecloud(conn=cxn)
            stop_featurecloud(conn=cxn)
        return


    @staticmethod
    def start_featurecloud_controllers(nodes):
        for cxn in nodes:
            launch_featurecloud(conn=cxn)
        return
    

    @staticmethod
    def stop_featurecloud_controllers(nodes):
        for cxn in nodes:
            stop_featurecloud(conn=cxn)
        return
    

    @staticmethod
    def create_and_join_project(coordinator, participants, tool):
        # create a new project with the coordinator node 
        coord_cxn = coordinator[0]
        fc_user = coord_cxn['fc_username']
        n_participants = len(participants)
        cmd = f"source .venv/bin/activate && python FedSim/create_project.py -u {fc_user} -t {tool} -p {n_participants}"
        stdout, stderr = execute_fabric(command=cmd, cxn=coord_cxn)
        
        # parse output for project ID and tokens
        lines = str(stdout).splitlines()
        project_id = None
        tokens = []
        for line in lines:
            if line.startswith("PROJECT:"):
                project_id = line.split("PROJECT:")[-1].strip()
            elif line.startswith("TOKEN:"):
                token = line.split("TOKEN:")[-1].strip()
                tokens.append(token)
        if project_id is None or len(tokens) != n_participants:
            raise ValueError("Failed to create project or retrieve tokens.")
        
        # use tokens to join project from participant nodes
        for cxn, token in zip(participants, tokens):
            fc_user = cxn['fc_username']
            cmd = f"source .venv/bin/activate && python FedSim/join_project.py -t {token} -u {fc_user} -p {project_id}"
            stdout, stderr = execute_fabric(command=cmd, cxn=cxn)
        return project_id


    @staticmethod
    def contribute_data_to_project(nodes, project_id):
        for cxn in nodes:
            fc_user = cxn['fc_username']
            cmd = f"source .venv/bin/activate && python FedSim/contribute_project.py -u {fc_user} -p {project_id}"
            stdout, stderr = execute_fabric(command=cmd, cxn=cxn)
        return
    

    @staticmethod
    def monitor_project_run(coordinator, project_id):
        cxn = coordinator[0]
        fc_user = cxn['fc_username']
        cmd = f"source .venv/bin/activate && python FedSim/monitor_project.py -u {fc_user} -p {project_id}"
        stdout, stderr = execute_fabric(command=cmd, cxn=cxn)
        return



    
def launch_featurecloud(conn: Connection):
    # launch featurecloud controller
    stop_featurecloud(conn=conn)  # ensure stopped before starting
    cmd = "source .venv/bin/activate && featurecloud controller start"
    stdout, stderr = execute_fabric(command=cmd, cxn=conn)
    assert is_controller_running(conn=conn), "Failed to start FeatureCloud controller"


def is_controller_running(conn: Connection):
    # check featurecloud status
    cmd = "source .venv/bin/activate && featurecloud controller status"
    stdout, stderr = execute_fabric(command=cmd, cxn=conn)
    if "running" in str(stdout).lower():
        return True
    else:
        return False


def stop_featurecloud(conn: Connection):
    # stop featurecloud controller
    cmd = "source .venv/bin/activate && featurecloud controller stop"
    stdout, stderr = execute_fabric(command=cmd, cxn=conn)
         
    
    