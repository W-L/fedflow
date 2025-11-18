#%%
from typing import List
import os
from pathlib import Path
import time

import httpx
from dotenv import load_dotenv

from logger import log
from utils import randstr

# %%
# %cd /home/lweilguny/proj/FedSim

load_dotenv(dotenv_path='.env', override=True)


        
#%%

TOOL_IDS = {
    "federated-svd": 85,
}



class Controller:

    def __init__(self, host="http://localhost:8000"):
        self.client = httpx.Client(base_url=host)
        self.host = host

    def controller_is_running(self) -> bool:
        try:
            r = self.client.get(f"{self.host}/ping/", timeout=2)
            return r.status_code == 200
        except httpx.RequestError:
            err_msg = "FeatureCloud controller is not running. Make sure to start it first."
            log(err_msg)
            return False


class Project: 

    def __init__(self, client):
        self.client = client
        
        
    @classmethod
    def from_project_id(cls, project_id: str, client):
        proj = cls(client=client)
        proj.project_id = project_id
        log(f"Using existing project {proj.project_id}.")
        log(f"Project status: {proj.get_status()}")
        return proj
        
        
    @classmethod
    def from_tool(cls, tool: str, client):
        proj = cls(client=client)
        proj.create_new_project()
        proj.set_project_workflow(tool=tool)
        log(f"Created new project {proj.project_id} {proj.project_name} with tool {proj.tool}.")
        log(f"Project status: {proj.get_status()}")
        return proj

    @classmethod
    def from_token(cls, token: str, project_id: str, client):
        proj = cls(client=client)
        proj.join_project(token=token)
        proj.project_id = project_id  # set the project ID after joining
        log(f"Joined existing project {proj.project_id} via token.")
        log(f"Project status: {proj.get_status()}")
        return proj
        
           


    def create_new_project(self):
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
        Update a project's workflow to include one federated tool.
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

        r = self.client.put(f"/api/projects/{self.project_id}/", json=payload)
        r.raise_for_status()
        return r.json()


    def create_project_tokens(self, n: int = 1):
        tokens = []
        for _ in range(n):
            r = self.client.post(f"/api/project-tokens/{self.project_id}/", json={"cmd": "create"})
            r.raise_for_status()
            tokens.append(r.json())   # contains id, token, project, etc.
        return tokens
    

    def join_project(self, token: str):
        payload = {"token": token, "cmd": "join"}
        r = self.client.post(f"/api/project-tokens/", json=payload)
        r.raise_for_status()
        return r.json()


    def get_status(self) -> str:
        r = self.client.get(f"/api/projects/{self.project_id}/")
        r.raise_for_status()
        data = r.json()
        status = data.get("status")
        return status


    def set_status(self, status: str):
        status_change = {"status": status}
        r = self.client.put(f"/api/projects/{self.project_id}/", json=status_change)
        r.raise_for_status()
        return r.json()
    

    def is_ready(self) -> bool:
        status = self.get_status()
        is_ready = status == "ready"
        return is_ready


    def is_prepping(self) -> bool:
        status = self.get_status()
        is_prepping = status == "prepare"
        return is_prepping
    

    def reset_project(self):
        self.set_status("ready")
        assert self.is_ready(), "Failed to reset project to ready."
        return True





class User: 

    def __init__(self, username):
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
        log(f"Logging in user {self.username}...")
        r = self.client.post("/api/auth/login/",
                             json={"username": self.username, "password": self.password})
        r.raise_for_status()
        data = r.json()
        self.access = data["access"]
        self.refresh = data["refresh"]
        self.client.headers["Authorization"] = f"Bearer {self.access}"
        

    def refresh_token(self):
        r = self.client.post("/api/auth/token/refresh/", json={"refresh": self.refresh})
        r.raise_for_status()
        self.access = r.json()["access"]
        self.client.headers["Authorization"] = f"Bearer {self.access}"


    def is_logged_in(self) -> bool:
        try:
            r = self.client.get("/api/user/info/")
            ok = r.status_code == 200
            log(f"User {self.username} logged in: {ok}")
            return ok
        except httpx.HTTPError:
            return False
        

    def get_site_info(self):
        r = self.client.get("/api/site/")
        r.raise_for_status()
        site_info = r.json()
        # write to file for the local controller
        with open("data/site_info.json", "w") as f:
            f.write(r.text)
        return site_info



class FCC:
    def __init__(self, user, project):
        # verify that controller is running
        self.controller = Controller()
        assert self.controller.controller_is_running()
        # attach objects
        self.project = project
        self.user = user
        
    


    def is_project_coordinator(self) -> bool:
        r = self.user.client.get(f"/api/projects/{self.project.project_id}/")
        r.raise_for_status()      # raise error if project doesn't exist
        data = r.json()
        role = data.get("role")
        is_coordinator = role == "coordinator"
        return is_coordinator



    def upload_files(self, filepaths: List[str]):
        # checking that we are in prepare mode
        is_prepping = self.project.is_prepping()
        if not is_prepping:
            if not self.is_project_coordinator():
                raise PermissionError("Only the project coordinator can set the project to 'prepare' mode.")
            
            log(f"Project {self.project.project_id} not in 'prepare' mode. Setting it now as coordinator.")
            self.project.set_status("prepare")
            time.sleep(2)  # wait a bit for status to update
            assert self.project.is_prepping(), "Failed to set project to 'prepare' mode."


        results = {}
        headers = {
            "Origin": "https://featurecloud.ai",
            "Accept": "application/json, text/plain, */*"
        }

        for idx, filepath in enumerate(filepaths):
            path = Path(filepath)
            file_name = path.name
            # finalize_flag = "true" if idx == len(filepaths) - 1 else ""
            params = {
                "projectId": self.project.project_id,
                "fileName": file_name,
                "finalize": "",
                "consent": ""
            }
            with open(path, "rb") as f:
                r = self.controller.client.post("/file-upload/", params=params, content=f.read(), headers=headers)
                r.raise_for_status()
                results[file_name] = r.text  # or r.json() if backend returns JSON
            time.sleep(2)  # to avoid overwhelming the server

        # finalize upload from this participant
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




    def monitor_project(self, interval=5, timeout=600):
        """
        Poll the project status until it changes from 'running'.
        - interval: seconds between polls
        - timeout: max total time in seconds
        """
        start_time = time.time()
        
        while True:
            # GET project info
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
        r = self.controller.client.get("/project-runs/", params={"projectId": self.project.project_id})
        r.raise_for_status()
        r_json = r.json()
        return r_json



    def _download_file(self, endpoint, filetype, out_dir, run, step):
        params = {"projectId": self.project.project_id, "step": step, "run": run}
        r = self.controller.client.get(endpoint, params=params)
        r.raise_for_status()

        filename = f"p{self.project.project_id}_r{run}_s{step}.{filetype}"
        filepath = Path(out_dir) / filename
        with open(filepath, "wb") as f:
            f.write(r.content)
        log(f"Downloaded {filepath}")
        return filepath
    

    

    def download_outcome(self, out_dir):    
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
            downloaded.append(logpath)
        # download result files
        for step in most_recent.get("resultSteps", []):
            resultpath = self._download_file(
                endpoint="/file-download/",
                filetype="zip",
                out_dir=out_dir,
                run=most_recent['runNr'],
                step=step
            )
            downloaded.append(resultpath)
        return downloaded








#%%
# user = User(username="p73wzaml9@mozmail.com")

# project_id = "17274"
# p1 = Project.from_project_id(project_id=project_id, client=user.client)
# p2 = Project.from_tool(tool="federated-svd", client=user.client)
# token = p2.create_project_tokens(n=1)[0]['token']

# user2 = User(username="flxt56ucr@mozmail.com")
# p3 = Project.from_token(token=token, project_id=p2.project_id, client=user2.client)



# %%
# fcc.upload_files(filepaths=["test_data/svd_solo/config.yaml",
                            # "test_data/svd_solo/mnist_200.tsv"])
# fcc.start_project()



#%%

# fcc.project.reset_project()


#%%




#%%
# fcc.download_outcome(out_dir="results/")


# %%



