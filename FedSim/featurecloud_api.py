from typing import List
import os
from pathlib import Path
import time

import httpx
from dotenv import load_dotenv

# %%
%cd ..

load_dotenv(dotenv_path='resources/.env', override=True)


        
#%%


class Controller:

    def __init__(self, host="http://localhost:8000"):
        self.client = httpx.Client(base_url=host)
        self.host = host

    def controller_is_running(self) -> bool:
        try:
            r = self.client.get(f"{self.host}/ping/", timeout=2)
            return r.status_code == 200
        except httpx.RequestError:
            return False


class Project: 

    def __init__(self, project_id: str, client):
        self.project_id = project_id
        self.client = client
        print(f"Project status: {self.get_status()}")


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

    def __init__(self, username, client):
        self.username = os.getenv(username)
        self.password = os.getenv(f"{username}_P")
        assert self.username is not None, f"Environment variable {username} not set."
        assert self.password is not None, f"Environment variable {username}_P not set."
        self.access = None
        self.refresh = None
        self.client = client


    def login(self):
        print(f"Logging in user {self.username}...")
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
            print(f"User {self.username} logged in: {ok}")
            return ok
        except httpx.HTTPError:
            return False



class FCC:
    def __init__(self, username, project_id):
        # verify that controller is running
        self.controller = Controller()
        err_msg = "FeatureCloud controller is not running. Make sure to start it first."
        assert self.controller.controller_is_running(), err_msg
        # create HTTP client
        self.client = httpx.Client(base_url="https://featurecloud.ai")
        # log in as user
        self.user = User(username=username, client=self.client)
        self.user.login()
        self.user.is_logged_in()
        # project object
        self.project = Project(project_id=project_id, client=self.client)
        
    


    def is_project_coordinator(self) -> bool:
        r = self.client.get(f"/api/projects/{self.project.project_id}/")
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
            
            print(f"Project {self.project.project_id} not in 'prepare' mode. Setting it now as coordinator.")
            self.project.set_status("prepare")
            time.sleep(2)  # wait a bit for status to update


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
        return results




    def start_project(self):
        """
        Signal the controller to finalize and start the project.
        No file content is sent; only the finalize flag is set.
        """
        params = {
            "projectId": self.project.project_id,
            "fileName": "",     # can be empty if no file is sent
            "finalize": "true", # triggers processing
            "consent": ""       # keep consistent with upload requests
        }
        headers = {
            "Origin": "https://featurecloud.ai",
            "Accept": "application/json, text/plain, */*"
        }

        r = self.controller.client.post("/file-upload/", params=params, headers=headers, content=b"")
        r.raise_for_status()
        # go into project monitoring mode
        end_status = self.monitor_project()
        print(end_status)
        return end_status



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
            print(f"Project {self.project.project_id} status: {status}")

            if status == 'prepare':
                time.sleep(interval)
                continue
            
            if status != "running":
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
        print(f"Downloaded {filepath}")
        return filepath
    

    

    def download_outcome(self, out_dir):
        Path(out_dir).mkdir(exist_ok=True, parents=True)
        runs = self._get_project_runs()
        print(f"Downloading files for project {self.project.project_id}...")
        most_recent = runs[0]  # assuming runs are sorted by recency
        print(f"Found {len(runs)} runs. Downloading most recent run, started on {most_recent['startedOn']}")

        
       
        for step in most_recent.get("logSteps", []):
            logpath = self._download_file(
                endpoint="/logs-download/",
                filetype="log",
                out_dir=out_dir,
                run=most_recent['runNr'],
                step=step
            ) 
        

        for step in most_recent.get("resultSteps", []):
            resultpath = self._download_file(
                endpoint="/file-download/",
                filetype="zip",
                out_dir=out_dir,
                run=most_recent['runNr'],
                step=step
            )
            
        return 




#%%


fcc = FCC(username="client0", project_id="17268")


# %%
# fcc.upload_files(filepaths=["test_data/svd_solo/config.yaml",
                            # "test_data/svd_solo/mnist_200.tsv"])
# fcc.start_project()



#%%

# fcc.project.reset_project()


#%%




#%%
fcc.download_outcome(out_dir="results/")


# %%
