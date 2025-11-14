from typing import List
import httpx
import os
from pathlib import Path

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


    def upload_files_raw(self, project_id: int, filepaths: List[str]):
        results = {}
        for idx, filepath in enumerate(filepaths):
            path = Path(filepath)
            file_name = path.name
            # finalize_flag = "true" if idx == len(filepaths) - 1 else ""
            params = {
                "projectId": project_id,
                "fileName": file_name,
                "finalize": "",
                "consent": ""
            }
            with open(path, "rb") as f:
                r = httpx.post(f"{self.host}/file-upload/", params=params, content=f.read())
                r.raise_for_status()
                results[file_name] = r.text  # or r.json() if backend returns JSON
        return results



    def get_available_files(self):
        r = httpx.get(f"{self.host}/get-files-from-mounted-volume/")
        r.raise_for_status()
        return r.json()  # likely a list of file names or dicts




class FCC:
    def __init__(self, username):
        # verify that controller is running
        self._verify_controller()
        self.client = httpx.Client(base_url="https://featurecloud.ai")
        self.username = os.getenv(username)
        self.password = os.getenv(f"{username}_P")
        assert self.username is not None, f"Environment variable {username} not set."
        assert self.password is not None, f"Environment variable {username}_P not set."
        self.access = None
        self.refresh = None
        


    def _verify_controller(self):
        self.controller = Controller()
        err_msg = "FeatureCloud controller is not running. Make sure to start it first."
        assert self.controller.controller_is_running(), err_msg


    def login(self):
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
            return r.status_code == 200
        except httpx.HTTPError:
            return False
        

    def project_is_ready(self, project_id: str) -> bool:
        r = self.client.get(f"/api/projects/{project_id}/")
        r.raise_for_status()      # raise error if project doesn't exist
        data = r.json()
        is_ready = data.get("status") == "ready"
        return is_ready


    def is_project_coordinator(self, project_id: str) -> bool:
        r = self.client.get(f"/api/projects/{project_id}/")
        r.raise_for_status()      # raise error if project doesn't exist
        data = r.json()
        role = data.get("role")
        is_coordinator = role == "coordinator"
        return is_coordinator


    def set_project_prepare(self, project_id: str):
        status_change = {"status": "prepare"}
        r = self.client.put(f"/api/projects/{project_id}/", json=status_change)
        r.raise_for_status()
        return r.json()
    

    def project_is_prepping(self, project_id: str) -> bool:
        r = self.client.get(f"/api/projects/{project_id}/")
        r.raise_for_status()      # raise error if project doesn't exist
        data = r.json()
        is_prepping = data.get("status") == "prepare"
        return is_prepping


    def stop_workflow(self, project_id: str):
        status_change = {"status": "ready"}
        r = self.client.put(f"/api/projects/{project_id}/", json=status_change)
        r.raise_for_status()
        assert self.project_is_ready(project_id), "Failed to reset project to ready."
        return r.json()





#%%


user = FCC(username="client0")
user.login()


# print(user.project_is_ready(project_id="17268"))
# print(user.is_project_coordinator(project_id="17268"))


# %%
print(user.project_is_prepping(project_id="17268"))

user.set_project_prepare(project_id="17268")

print(user.project_is_prepping(project_id="17268"))

user.stop_workflow(project_id="17268")

print(user.project_is_ready(project_id="17268"))



#%%

cont = Controller()

cont.controller_is_running()
cont.upload_files_raw(project_id=17268, filepaths=["data/federated_svd_split/mnist_split_0.tsv", "data/some_more_testing"])

files = cont.get_available_files()
print(files)

# %%
