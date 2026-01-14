import os
from pathlib import Path
import time

import httpx
from dotenv import load_dotenv

from fedflow.logger import log
from fedflow.utils import randstr



load_dotenv(dotenv_path='.env', override=True)
        

DEFAULT_HEADERS = {
    "User-Agent": "fedflow (https://github.com/W-L/fedflow)"
}





class RateLimiter:

    def __init__(self, rate: int = 3, per: int = 1):
        """
        :param rate: Max requests per unit time
        :param per: seconds
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.monotonic()



    def wait(self):
        now = time.monotonic()
        elapsed = now - self.last_check
        self.last_check = now

        self.allowance += elapsed * (self.rate / self.per)
        self.allowance = min(self.allowance, self.rate)

        if self.allowance < 1:
            sleep_time = (1 - self.allowance) * (self.per / self.rate)
            time.sleep(sleep_time)
            self.allowance = 0
        else:
            self.allowance -= 1






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
        self.limiter = RateLimiter() 


    def controller_is_running(self) -> bool:
        """
        Check whether the FeatureCloud controller is running

        :return: _description_
        """
        try:
            self.limiter.wait()
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
        self.limiter = RateLimiter()
        

        
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
    def from_tool(cls, app_id: int, client: httpx.Client):
        """
        Create a new Featurecloud project from the ID of an app

        :param app_id: ID of app on FeatureCloud
        :param client: httpx.Client connection of User
        :return: Project instance
        """
        proj = cls(client=client)
        proj.create_new_project()
        proj.set_project_workflow(app_id=app_id)
        log(f"Created new project {proj.project_id} {proj.project_name}")
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
        self.limiter.wait()
        r = self.client.post("/api/projects/", json=new_proj)
        r.raise_for_status()
        data = r.json()
        project_id = data.get("id")
        self.project_id = project_id


    def set_project_workflow(self, app_id: int):
        """
        Set an app to use in the workflow of a project.

        :param app_id: ID of the tool to use
        :raises ValueError: If the given tool is not implemented
        :return: json response
        """
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
                        "id": app_id
                    },
                    "order": 0,
                    "versionCertificationLevel": 1
                }
            ]
        }
        # send the payload to FeatureCloud
        self.limiter.wait()
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
            self.limiter.wait()
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
        self.limiter.wait()
        r = self.client.post("/api/project-tokens/", json=payload)
        r.raise_for_status()
        return r.json()


    def get_status(self) -> str:
        """
        Query the status of the project.

        :return: status description string
        """
        self.limiter.wait()
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
        self.limiter.wait()
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



class AppTable:

    def __init__(self):
        """
        Class to represent the app table on FeatureCloud
        """
        self.client = httpx.Client(base_url="https://featurecloud.ai", headers=DEFAULT_HEADERS)
        self.limiter = RateLimiter()
        self.apps = self._get_app_list()
        

    def _get_app_list(self) -> dict:
        """
        Get the list of available apps on FeatureCloud.ai

        :return: dict of app slugs and their IDs
        """
        self.limiter.wait()
        r = self.client.get("/api/apps/")
        r.raise_for_status()
        apps = r.json()
        # get dict of slugs to IDs
        apps = {app["slug"]: app["id"] for app in apps}
        return apps



class User: 

    def __init__(self, username: str):
        """
        Class to represent a Featurecloud user account

        :param username: name on FeatureCloud.ai
        """
        self.client = httpx.Client(base_url="https://featurecloud.ai", headers=DEFAULT_HEADERS)
        load_dotenv(dotenv_path='.env', override=True)
        self.username = username
        self.password = os.getenv(f"{username}")
        assert self.password is not None, f"Credentials for {username} not found."
        self.access = None
        self.refresh = None
        self.limiter = RateLimiter()
        # login as soon as user is created
        self.login()
        self.is_logged_in()
        self.get_site_info()
        # get the app list
        self.apps = AppTable().apps
        


    def login(self):
        """
        Login as this user
        """
        log(f"Logging in user {self.username}...")
        self.limiter.wait()
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
        self.limiter.wait()
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
            self.limiter.wait()
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
        self.limiter.wait()
        r = self.client.get("/api/site/")
        r.raise_for_status()
        site_info = r.json()
        # write to file for the local controller
        Path("data_fc").mkdir(parents=True, exist_ok=True)
        with open("data_fc/site_info.json", "w") as f:
            f.write(r.text)
        assert Path("data_fc/site_info.json").exists(), "Failed to write site_info.json"
        return site_info
    

    def get_purchased_apps(self) -> dict:
        """
        Get the list of apps owned by this user on FeatureCloud.ai

        :return: dict of app slugs and IDs
        """
        self.limiter.wait()
        r = self.client.get("/api/apps/purchase/")
        r.raise_for_status()
        apps = r.json()
        # get dict of slugs to IDs
        apps = {app["slug"]: app["id"] for app in apps}
        return apps

    
    def owns_app(self, slug: str) -> bool:
        """
        Check whether the user owns a specific app on FeatureCloud.ai

        :param slug: slug of the app to check
        :return: bool ownership
        """
        app_id = self.apps.get(slug)
        if app_id is None:
            raise ValueError(f"App {slug} invalid")
        owned_apps = self.get_purchased_apps()
        if app_id not in owned_apps.values():
            return False
        return True
    
    
    def purchase_app(self, slug: str):
        """
        purchase an app on FeatureCloud.ai

        :return: bool success
        """
        if self.owns_app(slug):
            log(f"User {self.username} already has app {slug}.")
            return True
        # add app to purchased apps
        app_id = self.apps.get(slug)
        self.limiter.wait()
        r = self.client.post(f"/api/apps/{app_id}/purchase/")
        r.raise_for_status()
        assert self.owns_app(slug), f"Failed to purchase app {slug} for user {self.username}."
        return True
    

    def remove_app(self, slug: str):
        """
        Remove an app from the purchased apps of this user

        :param slug: slug of the app to remove
        :return: bool success
        """
        app_id = self.apps.get(slug)
        if app_id is None:
            raise ValueError(f"App {slug} invalid")
        if not self.owns_app(slug):
            log(f"User {self.username} does not have app {slug}.")
            return True
        # remove app from purchased apps
        self.limiter.wait()
        r = self.client.delete(f"/api/apps/{app_id}/purchase/")
        r.raise_for_status()
        assert not self.owns_app(slug), f"Failed to remove app {slug} for user {self.username}."
        return True



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
        self.user.limiter.wait()
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
        if status in ["finished", "error", "failed", "stopped"]:
            self.project.reset_project()
            log(f"Project {self.project.project_id} reset to 'ready' status.")
        elif status == "running":
            raise PermissionError("Cannot upload files to a running project.")
        
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
        time.sleep(2)
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


    def monitor_project(self, interval: int = 5, timeout: int = 60) -> str:
        """
        Poll the project status until it changes from 'running'.

        :param interval: time between queries, defaults to 5
        :param timeout: maximum time to wait for project to finish, defaults to 60
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
                # stop the project through the api
                self.project.set_status("shutdown")
                time.sleep(5)
                status = self.project.get_status()
                if status == "stopped":
                    self.project.reset_project()

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
    # check if user owns the app otherwise purchase it
    app_id = user.apps.get(tool)
    if app_id is None:
        raise ValueError(f"App {tool} not found on FeatureCloud.ai, "
                         f"available apps: \n {list(user.apps.keys())}")
    if not user.owns_app(tool):
        user.purchase_app(tool)
        log(f"Added app {tool} to user {username}.")
    # proceed with project creation
    new_proj = Project.from_tool(app_id=app_id, client=user.client)
    tokens = new_proj.create_project_tokens(n=n_participants)
    log(f"\nPROJECT: {new_proj.project_id}")
    for t in tokens:
        log(f"TOKEN: {t['token']}")
    log("\n")




def contribute_data(username: str, project_id: str, data_list: list[str]):
    """
    Contribute data to a project

    :param username: username of the user contributing data
    :param project_id: ID of the project to contribute data to
    :param data_list: List of paths to be contributed
    """
    user = User(username=username)
    proj = Project.from_project_id(project_id=project_id, client=user.client)    
    fcc = FCC(user=user, project=proj)
    # upload all files in data_path
    # finalisation of upload is triggered at the end
    fcc.upload_files(filepaths=data_list)
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



def monitor_project(username: str, project_id: str, timeout: int = 60):
    """
    Monitor a running FeatureCloud project until status changes from 'running'.

    :param username: FeatureCloud username
    :param project_id: ID of the project to monitor
    :param timeout: maximum time to wait for project to finish, defaults to 60
    """
    user = User(username=username)
    proj = Project.from_project_id(project_id=project_id, client=user.client)    
    fcc = FCC(user=user, project=proj)
    # monitor the project run
    final_status = fcc.monitor_project(timeout=timeout)
    print(f"Project {project_id} status: {final_status}")
   


def query_project(username: str, project_id: str):
    """
    Query the status of a FeatureCloud project.

    :param username: FeatureCloud username
    :param project_id: ID of the project to monitor
    """
    user = User(username=username)
    proj = Project.from_project_id(project_id=project_id, client=user.client)    
    status = proj.get_status()
    log(f"{status}")
    
    
    
def download_project(username: str, project_id: str, out_dir: str):
    """
    Download logs and results of the most recent run of a FeatureCloud project.

    :param username: FeatureCloud username
    :param project_id: ID of the project to download from
    :param out_dir: Directory to save the output at
    """
    user = User(username=username)
    proj = Project.from_project_id(project_id=project_id, client=user.client)    
    fcc = FCC(user=user, project=proj)
    downloaded_files = fcc.download_outcome(out_dir=out_dir)
    log(f"Downloaded files to {out_dir}: \n{downloaded_files}")



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



def list_apps():
    """
    List available apps on FeatureCloud.ai
    """
    apps = AppTable().apps.keys()
    for app in apps:
        log(f"{app}")

