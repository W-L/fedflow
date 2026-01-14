from glob import glob
from pathlib import Path
import shutil
import shlex
import tarfile




class ClientManager:

    """
    Managing fabric Connections to remote hosts.
    """

    def __init__(self, serialg, threadg, clients: list):
        """
        Initialize the ClientManager.

        :param serialg: a group of fabric Connections
        :param threadg: a group of fabric Connections
        :param clients: a list of client information from the config file
        """
        self.serialg = serialg
        self.threadg = threadg
        # # remotes are separated into participants and coordinator
        self.participants = []
        self.coordinator = []
        # add some info from the config file to each connection
        for cxn_t, cxn_s, cinfo in zip(threadg, serialg, clients):
            user = cinfo.fc_username
            data = cinfo.data
            if cinfo.coordinator:
                cxn_t['coordinator'], cxn_s['coordinator'] = True, True
                cxn_t['fc_username'], cxn_s['fc_username'] = user, user
                cxn_t['data'], cxn_s['data'] = data, data
                self.coordinator.append(cxn_t)
            else:
                cxn_t['coordinator'], cxn_s['coordinator'] = False, False
                cxn_t['fc_username'], cxn_s['fc_username'] = user, user
                cxn_t['data'], cxn_s['data'] = data, data
                self.participants.append(cxn_t)
        


    def ping(self) -> None:
        """
        Ping all nodes to check connectivity.
        """
        cmd = 'echo "Ping from $(hostname)"'
        self.threadg.run(cmd)


    def run_bash_script(self, script_path: str) -> None:
        """
        Run a bash script on remotes. This is used to provision clients.

        :param script_path: path to the bash script to run
        """
        assert Path(script_path).is_file(), f"{script_path} is not a file."
        self.threadg.put(script_path, Path(script_path).name)
        cmd = f"bash {Path(script_path).name}"
        self.threadg.run(cmd)
    

    def install_package(self, reinstall: bool = False, nodeps: bool = False) -> None:
        """
        Install the package on all nodes.
        TODO this is used because the package is not on PyPI, so the wheel is transferred and installed locally.
        
        :param reinstall: whether to force reinstall the package
        :param nodeps: whether to skip installing dependencies
        """
        # find the wheel file for installation
        whl = glob("dist/fedflow-*.whl")[0]
        whl_name = Path(whl).name
        self.threadg.put(whl, remote=whl_name)
        self.threadg.run("python3 -m venv .venv")
        install_cmd = f"source .venv/bin/activate && pip install {whl_name}"
        if reinstall:
            install_cmd += " --force-reinstall"
        if nodeps:
            install_cmd += " --no-deps"
        self.threadg.run(install_cmd)
        

    def distribute_data(self) -> None:
        """
        Load the data defined in the config file onto all nodes.
        """
        for cxn in self.threadg:
            for local_path in cxn['data']:    
                cxn.put(local_path, remote=Path(local_path).name)


    def distribute_credentials(self, fc_creds: dict) -> None:
        """
        Transfer the credentials of the Featurecloud accounts to the remotes.

        :param fc_creds: dictionary of Featurecloud credentials
        """
        for cxn in self.threadg:
            fc_user = cxn['fc_username']
            fc_pass = fc_creds.get(fc_user, '')
            assert fc_user != '', "Featurecloud username is empty."
            assert fc_pass != '', f"Featurecloud password for user {fc_user} not found."
            cmd = f'echo {shlex.quote(fc_user)}={shlex.quote(fc_pass)} > .env'
            cxn.run(cmd, hide=True)


    def start_featurecloud_controllers(self) -> None:
        """
        Start the Featurecloud controller on all remotes.
        """
        self.stop_featurecloud_controllers()
        cmd = f"source .venv/bin/activate && featurecloud controller start --data-dir data_fc"
        self.threadg.run(f'echo "$(hostname): starting fc controller..." && {cmd}')
        # check status
        cmd = "source .venv/bin/activate && featurecloud controller status"
        results =self.threadg.run(cmd)
        ok = True
        failed = []
        for cxn, result in results.items():
            stdout = result.stdout
            if "running" not in str(stdout).lower():
                ok = False
                failed.append(cxn.host)
        assert ok, f'[{", ".join(failed)}] Failed to start FeatureCloud controller.'
                

    def stop_featurecloud_controllers(self) -> None:
        """
        Stop the Featurecloud controller on all remotes.
        """
        cmd = "source .venv/bin/activate && featurecloud controller stop"
        self.threadg.run(f'echo "$(hostname): stopping fc controller..." && {cmd}')
        

    def reset_clients(self,) -> None:
        """
        Reset all remotes by stopping any stray docker processes
        and removing all featurecloud data.
        """
        self.threadg.run('echo "Resetting $(hostname)..."')
        # stop docker containers
        stop_docker = "docker ps -q | xargs -r docker stop"
        self.threadg.run(stop_docker)
        # remove data directory if it exists
        # test that it's a directory and not a symlink before removing
        # this needs sudo because docker creates the directory as root?
        remove_featurecloud_remnants = "[ -d data_fc ] && [ ! -L data_fc ] && sudo rm -rf data_fc"
        self.threadg.run(remove_featurecloud_remnants, warn=True)


    def create_and_join_project(self, tool: str) -> str:
        """
        Use the featurecloud API to create a project with the coordinator node 
        and generate tokens for participants. Parse the tokens and used them on the participant nodes
        to join the project.

        :param tool: Name of the Featurecloud tool to use
        :raises ValueError: If project creation or token retrieval fails
        :return: The ID of the created project
        """
        # create a new project with the coordinator node 
        coord_cxn = self.coordinator[0]
        fc_user = coord_cxn['fc_username']
        n_participants = len(self.participants)
        cmd = f"source .venv/bin/activate && fcauto create -u {fc_user} -t {tool} -n {n_participants}"
        res = coord_cxn.run(f'echo "$(hostname): creating project with tool {tool}..." && {cmd}')
        # parse output for project ID and tokens
        lines = str(res.stdout).splitlines()
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
        for cxn, token in zip(self.participants, tokens):
            fc_user = cxn['fc_username']
            cmd = f"source .venv/bin/activate && fcauto join -t {token} -u {fc_user} -p {project_id}"
            cxn.run(f'echo "$(hostname): joining project {project_id}..." && {cmd}')
        return project_id


    def contribute_data_to_project(self, project_id: str) -> None:
        """
        Contribute data to a Featurecloud project from all participants.
        Finalizing the upload from all participants will trigger project execution.

        :param project_id: ID of the Featurecloud project
        """
        for cxn in self.serialg:
            fc_user = cxn['fc_username']
            # create a list of data paths to contribute
            data_paths = cxn['data']
            data_args = ' '.join([f"{Path(path).name}" for path in data_paths])
            cmd = f"source .venv/bin/activate && fcauto contribute -u {fc_user} -p {project_id} -d {data_args}"
            cxn.run(f'echo "$(hostname): contributing data to project {project_id}..." && {cmd}')
        return
    

    def monitor_project_run(self, coordinator: list, project_id: str, timeout: int = 60) -> None:
        """
        Monitor the status of a (running) project with the coordinator node.

        :param coordinator: Single-item list of fabric Connection for the coordinator node
        :param project_id: ID of the Featurecloud project to monitor
        :param timeout: Maximum time (in seconds) to wait for project completion
        :raises TimeoutError: If the project does not finish within the timeout period
        """
        cxn = coordinator[0]
        fc_user = cxn['fc_username']
        cmd = f"source .venv/bin/activate && fcauto monitor -u {fc_user} -p {project_id} -t {timeout}"
        cxn.run(cmd)
        

    def fetch_results(self, outdir, pid):
        """
        Fetch results from nodes

        :param outdir: local directory to save results to
        :param pid: ID of the Featurecloud project
        """
        for cxn in self.threadg:
            fcuser = cxn["fc_username"]
            local_dir = Path(f"{outdir}/{fcuser}")
            local_dir.mkdir(parents=True, exist_ok=True)
            archive_name = Path('data_fc.tar.gz')
            local_archive = local_dir / archive_name
            # Create archive remotely
            cxn.run(f"sudo tar -czf {archive_name} data_fc/")
            # Transfer archive
            cxn.get(archive_name, str(local_archive))
            # Extract locally
            with tarfile.open(local_archive, "r:gz") as tar:
                tar.extractall(local_dir)
            # cleanup
            cxn.run(f"rm -f {archive_name}")
            local_archive.unlink()
            # move the zip file with the actual results to a more convenient path
            raw_zip = Path(outdir) / fcuser / f"data_fc/workflows/Project_{pid}/Run_1/results_pr{pid}_run1_step1.zip"
            new_zip = Path(outdir) / f"results_{fcuser}.zip"
            if raw_zip.is_file():
                shutil.copy2(raw_zip, new_zip)


