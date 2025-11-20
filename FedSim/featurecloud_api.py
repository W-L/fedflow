from glob import glob
import os
from pathlib import Path
import time

import httpx
from dotenv import load_dotenv

from logger import log
from utils import randstr



load_dotenv(dotenv_path='.env', override=True)
        

TOOL_IDS = {
    "federated-svd": 85,
    "random-forest": 50,
    "mean-app": 66,
}



class Controller:

    """
    Class for the communication with the local FeatureCloud controller
    """

    def __init__(self, host: str ="http://localhost:8000"):
        """
        Initialize connection to the local controller   

        :param host: The host URL of the local controller
        """
        self.client = httpx.Client(base_url=host)
        self.host = host


    def controller_is_running(self) -> bool:
        """
        Check whether the FeatureCloud controller is running

        :return: _description_
        """
        try:
            r = self.client.get(f"{self.host}/ping/", timeout=2)
            return r.status_code == 200
        except httpx.RequestError:
            err_msg = "FeatureCloud controller is not running. Make sure to start it first."
            log(err_msg)
            return False



class Project: 

    """
    Class that represents a FeatureCloud Project
    """

    def __init__(self, client: httpx.Client):
        self.client = client
        

        
    @classmethod
    def from_project_id(cls, project_id: str, client: httpx.Client):
        """
        Attach to an existing FeatureCloud project by numeric ID

        :param project_id: Persistent numeric ID of project
        :param client: httpx.Client connection of User
        :return: Project instance
        """
        proj = cls(client=client)
        proj.project_id = project_id
        log(f"Using existing project {proj.project_id}.")
        log(f"Project status: {proj.get_status()}")
        return proj
        
        
    @classmethod
    def from_tool(cls, tool: str, client: httpx.Client):
        """
        Create a new Featurecloud project from the name of a tool

        :param tool: name of a FeatureCloud tool
        :param client: httpx.Client connection of User
        :return: Project instance
        """
        proj = cls(client=client)
        proj.create_new_project()
        proj.set_project_workflow(tool=tool)
        log(f"Created new project {proj.project_id} {proj.project_name} with tool {proj.tool}.")
        log(f"Project status: {proj.get_status()}")
        return proj
    

    @classmethod
    def from_token(cls, token: str, project_id: str, client: httpx.Client):
        """
        Instantiate a project by joining it with a token.

        :param token: Participant token used to join
        :param project_id: Numeric ID of the project
        :param client: httpx.Client connection of User
        :return: Project instance
        """
        proj = cls(client=client)
        proj.join_project(token=token)
        proj.project_id = project_id  # set the project ID after joining
        log(f"Joined existing project {proj.project_id} via token.")
        log(f"Project status: {proj.get_status()}")
        return proj
        
        
    def create_new_project(self):
        """
        Create a new FeatureCloud project with a randomized name.
        """
        self.project_name = randstr()
        new_proj = {
            "name": self.project_name,
            "description": "",
            "status": ""
        }
        r = self.client.post("/api/projects/", json=new_proj)
        r.raise_for_status()
        data = r.json()
        project_id = data.get("id")
        self.project_id = project_id


    def set_project_workflow(self, tool: str):
        """
        Set a tool to use in the workflow of a project.        

        :param tool: Name of the tool to use
        :raises ValueError: If the given tool is not implemented
        :return: json response
        """
        self.tool = tool
        try:
            tool_id = TOOL_IDS[tool]
        except KeyError:
            raise ValueError(f"{tool} not available. Available: {list(TOOL_IDS.keys())}")

        payload = {
            "id": self.project_id,
            "name": self.project_name,
            "description": "",
            "status": "ready",   # the workflow can be added in multiple steps, then the status is 'init' first
            "workflow": [
                {
                    "id": 0,
                    "projectId": self.project_id,
                    "federatedApp": {
                        "id": tool_id
                    },
                    "order": 0,
                    "versionCertificationLevel": 1
                }
            ]
        }
        # send the payload to FeatureCloud
        r = self.client.put(f"/api/projects/{self.project_id}/", json=payload)
        r.raise_for_status()
        return r.json()


    def create_project_tokens(self, n: int = 0) -> list[dict]:
        """
        Create project tokens for the current project.

        :param n: number of tokens to generate, defaults to 0
        :return: list of tokens
        """
        tokens = []
        for _ in range(n):
            r = self.client.post(f"/api/project-tokens/{self.project_id}/", json={"cmd": "create"})
            r.raise_for_status()
            tokens.append(r.json())   # contains id, token, project, etc.
        return tokens
    

    def join_project(self, token: str):
        """
        Use a project token to join

        :param token: Participant token
        :return: json string
        """
        payload = {"token": token, "cmd": "join"}
        r = self.client.post(f"/api/project-tokens/", json=payload)
        r.raise_for_status()
        return r.json()


    def get_status(self) -> str:
        """
        Query the status of the project.

        :return: status description string
        """
        r = self.client.get(f"/api/projects/{self.project_id}/")
        r.raise_for_status()
        data = r.json()
        status = data.get("status")
        return status


    def set_status(self, status: str):
        """
        Set a status on the project. E.g. used to reset a project

        :param status: string describing the status
        :return: json response
        """
        status_change = {"status": status}
        r = self.client.put(f"/api/projects/{self.project_id}/", json=status_change)
        r.raise_for_status()
        return r.json()
    

    def is_ready(self) -> bool:
        """
        Check if a project is in the 'ready' state

        :return: boolean marker
        """
        status = self.get_status()
        is_ready = status == "ready"
        return is_ready


    def is_prepping(self) -> bool:
        """
        Check if project is in the 'prepare' state

        :return: boolean marker
        """
        status = self.get_status()
        is_prepping = status == "prepare"
        return is_prepping
    

    def reset_project(self) -> bool:
        """
        Set the status to 'ready'. E.g. used to reset a failed or finished project

        :return: boolean marker
        """
        self.set_status("ready")
        assert self.is_ready(), "Failed to reset project to ready."
        return True




class User: 

    def __init__(self, username: str):
        """
        Class to represent a Featurecloud user account

        :param username: name on FeatureCloud.ai
        """
        self.client = httpx.Client(base_url="https://featurecloud.ai")
        self.username = username
        self.password = os.getenv(f"{username}")
        assert self.password is not None, f"Credentials for {username} not found."
        self.access = None
        self.refresh = None
        # login as soon as user is created
        self.login()
        self.is_logged_in()
        self.get_site_info()
        


    def login(self):
        """
        Login as this user
        """
        log(f"Logging in user {self.username}...")
        r = self.client.post("/api/auth/login/",
                             json={"username": self.username, "password": self.password})
        r.raise_for_status()
        data = r.json()
        self.access = data["access"]
        self.refresh = data["refresh"]
        self.client.headers["Authorization"] = f"Bearer {self.access}"
        

    def refresh_token(self):
        """
        Method to refresh a temporary token. Currently unused.
        """
        r = self.client.post("/api/auth/token/refresh/", json={"refresh": self.refresh})
        r.raise_for_status()
        self.access = r.json()["access"]
        self.client.headers["Authorization"] = f"Bearer {self.access}"


    def is_logged_in(self) -> bool:
        """
        Check if user is logged in by trying to access its info

        :return: True if logged in
        """
        try:
            r = self.client.get("/api/user/info/")
            ok = r.status_code == 200
            log(f"User {self.username} logged in: {ok}")
            return ok
        except httpx.HTTPError:
            return False
        

    def get_site_info(self):
        """
        Download the site_info.json marker file used by the controller

        :return: json snippet
        """
        r = self.client.get("/api/site/")
        r.raise_for_status()
        site_info = r.json()
        # write to file for the local controller
        with open("data/site_info.json", "w") as f:
            f.write(r.text)
        return site_info



class FCC:

    def __init__(self, user: User, project: Project):
        """
        Class to represent a User acting within a specific project

        :param user: User instance
        :param project: Project instance
        """
        # verify that controller is running
        self.controller = Controller()
        assert self.controller.controller_is_running()
        # attach objects
        self.project = project
        self.user = user
        

    def is_project_coordinator(self) -> bool:
        """
        Check if the attached User is the project coordinator

        :return: True if user is coordinator
        """
        r = self.user.client.get(f"/api/projects/{self.project.project_id}/")
        r.raise_for_status()      # raise error if project doesn't exist
        data = r.json()
        role = data.get("role")
        is_coordinator = role == "coordinator"
        return is_coordinator


    def upload_files(self, filepaths: list[str]) -> dict:
        """
        Upload files to a project as a specific FeatureCloud User

        :param filepaths: paths to the files to upload
        :raises PermissionError: First data upload needs to be done from the coordinator
        :return: dict of booleans for each uploaded file
        """
        # check the project status first
        # to allow file contributions, project needs to be in 'prepare' state
        # 'prepare' can only be reached from 'ready'
        status = self.project.get_status()
        log(f"Project {self.project.project_id} status: {status}")
        if status in ["finished", "error", "failed"]:
            self.project.reset_project()
            log(f"Project {self.project.project_id} reset to 'ready' status.")
        
        # checking that we are in prepare mode
        is_prepping = self.project.is_prepping()
        if not is_prepping:
            if not self.is_project_coordinator():
                raise PermissionError("Only the project coordinator can set the project to 'prepare' mode.")
            # if not try to progress to 'prepare' state    
            log(f"Project {self.project.project_id} not in 'prepare' mode. Setting it now as coordinator.")
            self.project.set_status("prepare")
            time.sleep(2)  # wait a bit for status to update
            assert self.project.is_prepping(), "Failed to set project to 'prepare' mode."

        # collect confirmations from all uploads
        results = {}
        headers = {
            "Origin": "https://featurecloud.ai",
            "Accept": "application/json, text/plain, */*"
        }
        
        # upload all data
        for filepath in filepaths:
            path = Path(filepath)
            file_name = path.name
            params = {
                "projectId": self.project.project_id,
                "fileName": file_name,
                "finalize": "",
                "consent": ""
            }
            with open(path, "rb") as f:
                # files are 'uploaded' to the controller, not to FeatureCloud
                r = self.controller.client.post("/file-upload/", params=params, content=f.read(), headers=headers)
                r.raise_for_status()
                results[file_name] = r.text  # or r.json() if backend returns JSON
            time.sleep(2)  # to avoid overwhelming the server

        # finalize upload from this participant
        # setting the 'finalize' flag finishes the upload from a single participant
        time.sleep(5)
        params = {
            "projectId": self.project.project_id,
            "fileName": "",     
            "finalize": "true", # triggers processing
            "consent": ""       
        }
        r = self.controller.client.post("/file-upload/", params=params, headers=headers, content=b"")
        r.raise_for_status()
        time.sleep(2)
        return results


    def monitor_project(self, interval: int = 5, timeout: int = 600) -> str:
        """
        Poll the project status until it changes from 'running'.

        :param interval: time between queries, defaults to 5
        :param timeout: maximum time to wait for project to finish, defaults to 600
        :raises TimeoutError: if not finishing within timeout
        :return: final status
        """
        start_time = time.time()
        
        while True:
            # query the project status
            status = self.project.get_status()
            log(f"Project {self.project.project_id} status: {status}")
            
            if status == 'prepare':
                time.sleep(interval)
                continue
            
            if status != "running":
                log(f"Project {self.project.project_id} ended with status: {status}")
                return status  # finished, failed, or any other state
            
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Project {self.project.project_id} did not finish within {timeout} seconds.")

            time.sleep(interval)



    def _get_project_runs(self):
        """
        Query the controller for the number of runs of the project that have been executed

        :return: json snippet
        """
        r = self.controller.client.get("/project-runs/", params={"projectId": self.project.project_id})
        r.raise_for_status()
        r_json = r.json()
        return r_json



    def _download_file(self, endpoint: str, filetype: str, out_dir: str, run: int, step: int) -> Path:
        """
        Generic method to download a file from the controller client

        :param endpoint: URL endpoint to query
        :param filetype: Differs for logs and results
        :param out_dir: Directory to store output in
        :param run: Which number of run to download from
        :param step: Which step of project to download for
        :return: Path of the downloaded file
        """
        params = {"projectId": self.project.project_id, "step": step, "run": run}
        r = self.controller.client.get(endpoint, params=params)
        r.raise_for_status()

        filename = f"p{self.project.project_id}_r{run}_s{step}.{filetype}"
        filepath = Path(out_dir) / filename
        with open(filepath, "wb") as f:
            f.write(r.content)
        log(f"Downloaded {filepath}")
        return filepath
    

    def download_outcome(self, out_dir: str) -> list[str]:
        """
        Download the log and result files of the most recent run of the attached project.

        :param out_dir: Directory to save the output at
        :return: list of downloaded files
        """
        Path(out_dir).mkdir(exist_ok=True, parents=True)
        runs = self._get_project_runs()
        log(f"Downloading files for project {self.project.project_id}...")
        most_recent = runs[0]  # assuming runs are sorted by recency
        log(f"Found {len(runs)} run(s). Downloading most recent run, started on {most_recent['startedOn']}")
        # download log files    
        downloaded = []   
        for step in most_recent.get("logSteps", []):
            logpath = self._download_file(
                endpoint="/logs-download/",
                filetype="log",
                out_dir=out_dir,
                run=most_recent['runNr'],
                step=step
            ) 
            downloaded.append(str(logpath))
        # download result files
        for step in most_recent.get("resultSteps", []):
            resultpath = self._download_file(
                endpoint="/file-download/",
                filetype="zip",
                out_dir=out_dir,
                run=most_recent['runNr'],
                step=step
            )
            downloaded.append(str(resultpath))
        return downloaded



# The following functions are used by the subcommands in the command-line interface
def create_project_and_tokens(username: str, tool: str, n_participants: int):
    """
    Create a new project on Featurecloud.ai and generate participant tokens.

    :param username: Username of the user creating the project.
    :param tool: Tool to be used in the project.
    :param n_participants: Number of participant tokens to create.
    """
    user = User(username=username)
    new_proj = Project.from_tool(tool=tool, client=user.client)
    tokens = new_proj.create_project_tokens(n=n_participants)
    log(f"\nPROJECT: {new_proj.project_id}")
    for t in tokens:
        log(f"TOKEN: {t['token']}")
    log(f"\n")




def contribute_data(username: str, project_id: str, data_path: str):
    """
    Contribute data to a project

    :param username: username of the user contributing data
    :param project_id: ID of the project to contribute data to
    :param data_path: Path to the data to be contributed
    """
    user = User(username=username)
    proj = Project.from_project_id(project_id=project_id, client=user.client)    
    fcc = FCC(user=user, project=proj)
    # upload all files in data_path
    # finalisation of upload is triggered at the end
    files_to_upload = list(glob(f"{data_path}/*"))
    fcc.upload_files(filepaths=files_to_upload)
    # the project starts when all participants have uploaded their data
    print(f"{username} uploaded data to project {project_id}")



def join_project(username: str, token: str, project_id: str):
    """
    Join a FeatureCloud project using a token generated during project creation.

    :param username: FeatureCloud username
    :param token: Project participation token
    :param project_id: Numeric ID of the project to join
    """
    user = User(username=username)
    joined_proj = Project.from_token(token=token, project_id=project_id, client=user.client)
    log(f"{username} joined project: {joined_proj.project_id}")



def monitor_project(username: str, project_id: str):
    """
    Monitor a running FeatureCloud project until status changes from 'running'.

    :param username: FeatureCloud username
    :param project_id: ID of the project to monitor
    """
    user = User(username=username)
    proj = Project.from_project_id(project_id=project_id, client=user.client)    
    fcc = FCC(user=user, project=proj)
    # monitor the project run
    final_status = fcc.monitor_project()
    print(f"Project {project_id} status: {final_status}")
    time.sleep(5)
    # download outcome
    out_dir = 'results/'
    downloaded_files = fcc.download_outcome(out_dir=out_dir)
    print(f"Run finished with status {final_status}. Logs (& Results) downloaded to {out_dir}: \n{downloaded_files}")
   


def reset_project(username: str, project_id: str):
    """
    Reset a FeatureCloud project to 'ready' status.

    :param username: FeatureCloud username
    :param project_id: ID of the project to reset
    """
    user = User(username=username)
    proj = Project.from_project_id(project_id=project_id, client=user.client)    
    proj.reset_project()
    log(f"Project {project_id} has been reset to 'ready' status.")


