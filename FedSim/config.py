#%%
import os
import rtoml
from fabric import SerialGroup
from dotenv import load_dotenv

from logger import logger


class Config:

    def __init__(self, toml_path: str):
        # load config from toml file
        self.toml_path = toml_path
        with open(toml_path, "r") as f:
            self.config = rtoml.load(f)
        # set the clients
        self.n = len(self.config['clients'])
        self.fc_users = self.get_fc_users()
        self.fc_creds = self.load_fc_credentials()
        self.data_paths = self.get_data_paths()

        
    def construct_client_strings(self) -> list[str]:
        client_strings = []
        for cname, cinfo in self.config['clients'].items():
            cstr = f"{cinfo['username']}@{cinfo['hostname']}"
            if cinfo['port'] != '' and cinfo['port'] is not None:
                cstr += f":{cinfo['port']}"
            client_strings.append(cstr)
        logger.info(f"client strings: {client_strings}")
        return client_strings


    def get_sshkeys(self) -> list[str]:
        sshkeys = []
        for cname, cinfo in self.config['clients'].items():
            sshkey = cinfo.get('sshkey', None)
            sshkeys.append(sshkey)
        return sshkeys


    def construct_serialgroup(self):
        # generate the client strings
        client_strings = self.construct_client_strings()
        sshkeys = self.get_sshkeys()
        self.serialg = SerialGroup(*client_strings, connect_kwargs={"key_filename": sshkeys})
        logger.info(f"serial group: {self.serialg}")
        return self.serialg


    def get_fc_users(self) -> list[str]:
        users = []
        for cname, cinfo in self.config['clients'].items():
            fc_user = cinfo.get('fc_username', None)
            users.append(fc_user)
        return users


    def get_data_paths(self) -> list[str]:
        data_paths = []
        for cname, cinfo in self.config['clients'].items():
            data_path = cinfo.get('data', None)
            data_paths.append(data_path)
        return data_paths
    

    def load_fc_credentials(self):
        load_dotenv(dotenv_path='.env', override=True)
        fc_cred = {}
        for fc_user in self.fc_users:
            fc_pass = os.getenv(f"{fc_user}")
            assert fc_user is not None and fc_pass is not None, f"credentials {fc_user} not found"
            fc_cred[fc_user] = fc_pass
        return fc_cred
    

#%%

# conf = Config(toml_path="resources/config_svd_solo.toml")

# %%
