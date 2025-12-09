from glob import glob
from pathlib import Path
import time

import fedsim.utils_fabric as utils_fabric
from fedsim.utils import execute_fabric
from fedsim.logger import log



class ClientManager:

    """
    Managing fabric Connections to remote hosts.
    """

    def __init__(self, serialgroup, clients: dict):
        """
        Initialize the ClientManager.

        :param serialgroup: a group of fabric Connections
        :param clients: a dictionary of client information from the config file
        """
        # remotes are separated into participants and coordinator
        self.participants = []
        self.coordinator = []
        # add some info from the config file to each connection
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
        # list of all nodes to apply operations to
        self.all = self.coordinator + self.participants



    def _nodes_or_all(self, nodes = None) -> list:
        return nodes if nodes is not None else self.all



    def ping(self, nodes = None) -> None:
        """
        Ping all nodes to check connectivity.

        :param nodes: list of fabric Connections to ping
        """
        for cxn in self._nodes_or_all(nodes):
            try:
               cmd = 'echo "Ping from $(hostname)"'
               _ = execute_fabric(cmd, cxn)
            except Exception as e:
                log(f"Error during ping of {cxn.get('host', '')}: {e}")
        return
    


    def install_package(self, nodes = None, reinstall: bool = False, nodeps: bool = False) -> None:
        """
        Install the fedsim package on all nodes.
        TODO this is used because the package is not on PyPI, so the wheel is transferred and installed locally.

        :param nodes: list of fabric Connections to install package on
        :param reinstall: whether to force reinstall the package
        :param nodeps: whether to skip installing dependencies
        """
        for cxn in self._nodes_or_all(nodes):
            # find the wheel file for installation
            whl = glob("dist/fedsim-*.whl")[0]
            utils_fabric.upload_file(
                conn=cxn,
                local_path=whl,
                remote_path=f"{Path(whl).name}",
                force=True
            )
            cxn.run("python3 -m venv .venv")
            install_cmd = f"source .venv/bin/activate && pip install {Path(whl).name}"
            if reinstall:
                install_cmd += " --force-reinstall"
            if nodeps:
                install_cmd += " --no-deps"
            cxn.run(install_cmd)
            # execute_fabric(command=install_cmd, cxn=cxn)
        return

    

    def distribute_data(self, nodes = None) -> None:
        """
        Load the data defined in the config file onto all nodes.

        :param nodes: list of fabric Connections to distribute data to
        """
        for cxn in self._nodes_or_all(nodes):
            # data from the config file
            utils_fabric.transfer_with_packing(conn=cxn, paths=cxn['data'])



    def distribute_credentials(self, fc_creds: dict, nodes = None) -> None:
        """
        Transfer the credentials of the Featurecloud accounts to the remotes.

        :param fc_creds: dictionary of Featurecloud credentials
        :param nodes: list of fabric Connections to distribute credentials to
        """
        for cxn in self._nodes_or_all(nodes):
            fc_user = cxn['fc_username']
            fc_pass = fc_creds.get(fc_user, '')
            utils_fabric.write_to_file_remote(
                conn=cxn,
                remote_path=f".env",
                content=f"{fc_user}={fc_pass}\n"
            )



    def test_featurecloud_controllers(self, nodes = None) -> None:
        """
        Test launching and stopping the Featurecloud controllers.

        :param nodes: list of fabric Connections to test
        """
        for cxn in self._nodes_or_all(nodes):
            utils_fabric.launch_featurecloud(conn=cxn)
            utils_fabric.stop_featurecloud(conn=cxn)
        return



    def start_featurecloud_controllers(self, nodes = None) -> None:
        """
        Start the Featurecloud controller on multiple remotes.

        :param nodes: list of fabric Connections to start controllers on
        """
        for cxn in self._nodes_or_all(nodes):
            utils_fabric.launch_featurecloud(conn=cxn)
        return
    


    def stop_featurecloud_controllers(self, nodes = None) -> None:
        """
        Stop the Featurecloud controller on multiple remotes.

        :param nodes: list of fabric Connections to stop controllers on
        """
        for cxn in self._nodes_or_all(nodes):
            utils_fabric.stop_featurecloud(conn=cxn)
        return
    


    def create_and_join_project(self, coordinator: list, participants: list, tool: str) -> str:
        """
        Use the featurecloud API to create a project with the coordinator node 
        and generate tokens for participants. Parse the tokens and used them on the participant nodes
        to join the project.

        :param coordinator: Single-item list of fabric Connection for the coordinator node
        :param participants: list of fabric Connections for participant nodes
        :param tool: Name of the Featurecloud tool to use
        :raises ValueError: If project creation or token retrieval fails
        :return: The ID of the created project
        """
        # create a new project with the coordinator node 
        coord_cxn = coordinator[0]
        fc_user = coord_cxn['fc_username']
        n_participants = len(participants)
        cmd = f"source .venv/bin/activate && fcauto create -u {fc_user} -t {tool} -n {n_participants}"
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
            cmd = f"source .venv/bin/activate && fcauto join -t {token} -u {fc_user} -p {project_id}"
            stdout, stderr = execute_fabric(command=cmd, cxn=cxn)
        return project_id



    def contribute_data_to_project(self, project_id: str, nodes = None) -> None:
        """
        Contribute data to a Featurecloud project from all participants.
        Finalizing the upload from all participants will trigger project execution.

        :param nodes: list of fabric Connections to contribute data from
        :param project_id: ID of the Featurecloud project
        """
        for cxn in self._nodes_or_all(nodes):
            fc_user = cxn['fc_username']
            # create a list of data paths to contribute
            data_paths = cxn['data']
            data_args = ' '.join([f"{Path(path).name}" for path in data_paths])
            cmd = f"source .venv/bin/activate && fcauto contribute -u {fc_user} -p {project_id} -d {data_args}"
            stdout, stderr = execute_fabric(command=cmd, cxn=cxn)
        return
    


    def monitor_project_run(self, coordinator: list, project_id: str, interval: int = 5, timeout: int = 600) -> None:
        """
        Monitor the status of a (running) project with the coordinator node.

        :param coordinator: Single-item list of fabric Connection for the coordinator node
        :param project_id: ID of the Featurecloud project to monitor
        :param interval: Time interval (in seconds) between status checks
        :param timeout: Maximum time (in seconds) to wait for project completion
        :raises TimeoutError: If the project does not finish within the timeout period
        """
        cxn = coordinator[0]
        fc_user = cxn['fc_username']
        cmd = f"source .venv/bin/activate && fcauto monitor -u {fc_user} -p {project_id}"
        result = cxn.run(cmd)
        log(f'[{cxn.host}] STDOUT: {result.stdout}')
        if result.stderr.strip() != "":
            log(f'[{cxn.host}] STDERR: \n{result.stderr}\n')
        


    
