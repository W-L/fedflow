import os
from types import SimpleNamespace

import rtoml
from fabric import SerialGroup, ThreadingGroup
from dotenv import load_dotenv

from fedflow.logger import log



class Config:

    def __init__(self, toml_path: str):
        """
        Load configuration from a toml file. 
        Init and creation of SerialGroup are the only public methods.

        :param toml_path: path to the toml config file
        """
        self.toml_path = toml_path
        with open(toml_path, "r") as f:
            self.config = rtoml.load(f)
        # grab client information
        self.n = len(self.config['clients'])
        self.fc_users = self._get_fc_users()
        self.fc_creds = self._load_fc_credentials()
        self.data_paths = self._get_data_paths()
        # set general options
        self.is_simulated = self.config['general'].get('sim', False)
        self.outdir = self.config['general'].get('outdir', 'results/')
        # set debug options
        debug = self.config.get('debug', {})
        self.debug = SimpleNamespace()
        self.debug.reinstall = debug.get('reinstall', True)
        self.debug.nodeps = debug.get('nodeps', False)
        self.debug.timeout = debug.get('timeout', 60)
        self.debug.vmonly = debug.get('vmonly', False)

        

    def _construct_client_strings(self) -> list[str]:
        """
        Generate strings for ssh connection to remote clients. 
        I.e. "user@hostname:port"

        :return: list of client connection strings
        """
        client_strings = []
        for cinfo in self.config['clients'].values():
            cstr = f"{cinfo['username']}@{cinfo['hostname']}"
            port = cinfo.get('port', None)
            if port:
                cstr += f":{port}"
            client_strings.append(cstr)
        log(f"client strings: {client_strings}")
        return client_strings



    def _get_sshkeys(self) -> list[str]:
        """
        Grab the paths to ssh private keys for the remote connections

        :return: list of ssh key paths
        """
        sshkeys = []
        for cinfo in self.config['clients'].values():
            sshkey = cinfo.get('sshkey', None)
            sshkeys.append(sshkey)
        return sshkeys



    def _get_fc_users(self) -> list[str]:
        """
        Grab the Featurecloud usernames of each client from the config file.

        :return: list of Featurecloud users
        """
        users = []
        for cinfo in self.config['clients'].values():
            fc_user = cinfo.get('fc_username', None)
            users.append(fc_user)
        return users



    def _get_data_paths(self) -> list[str]:
        """
        Grab the paths to the data contributed by each client.

        :return: list of paths
        """
        data_paths = []
        for cinfo in self.config['clients'].values():
            data_path = cinfo.get('data', None)
            data_paths.append(data_path)
        return data_paths
    


    def _load_fc_credentials(self) -> dict[str, str]:
        """
        Load the Featurecloud credentials of all clients from an environment file.

        :return: dictionary of Featurecloud credentials
        """
        load_dotenv(dotenv_path='.env', override=True)
        load_dotenv(dotenv_path='tests/env', override=True)
        fc_cred = {}
        for fc_user in self.fc_users:
            # if not fc_user:  # if coordinator does not contribute data
            #     log('no Featurecloud user specified for a client, skipping credential load')
            #     continue
            fc_pass = os.getenv(f"{fc_user}")
            assert fc_pass is not None, f"credentials {fc_user} not found"
            fc_cred[fc_user] = fc_pass
        return fc_cred
    

    
    def construct_connection_group(self) -> tuple[SerialGroup, ThreadingGroup]:
        """
        Generate a group of fabric Connections from the info in the config file.
        This is used when the target remotes are actual machines instead of vagrant VMs.

        :return: SerialGroup of fabric Connections
        """
        # generate the client strings
        client_strings = self._construct_client_strings()
        # grab ssh keys for connect_kwargs
        sshkeys = self._get_sshkeys()
        self.serialg = SerialGroup(*client_strings, connect_kwargs={"key_filename": sshkeys})
        self.threadg = ThreadingGroup(*client_strings, connect_kwargs={"key_filename": sshkeys})
        log(f"serial group: {self.serialg}")
        return self.serialg, self.threadg


    
