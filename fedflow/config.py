import os
import sys
from pathlib import Path
import tomllib

from fabric import SerialGroup, ThreadingGroup
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
import tomli_w # type: ignore

from fedflow.logger import log



class DebugConfig(BaseModel):
    reinstall: bool = True
    nodeps: bool = False
    timeout: int = 60 * 60
    vmonly: bool = False


class ClientConfig(BaseModel):
    fc_username: str = 'FC_USER'
    data: list[str] = []
    coordinator: bool = False
    username: str = 'USER'
    hostname: str = 'HOSTNAME'
    port: int | None = None
    sshkey: str = '.ssh/id_rsa'


class GeneralConfig(BaseModel):
    project_id: int | None = 0
    tool: str | None = ''
    sim: bool = False
    outdir: str = 'results/'
    debug: DebugConfig | None = None
    clients: list[ClientConfig] = [ClientConfig(), ClientConfig()]

    


    

class Config:

    def __init__(self, toml: str):
        """
        Load configuration from a toml file. 
        Init and creation of SerialGroup are the only public methods.

        :param toml: path to toml config file
        """
        try:
            self.config = self._load_config(Path(toml))
        except ValidationError as e:
            print("Invalid configuration:")
            print(e)
            sys.exit(1)
        
        # grab client information
        self.n = len(self.config.clients)
        self.fc_users = [c.fc_username for c in self.config.clients]
        self.data_paths = [c.data for c in self.config.clients]
        self.fc_creds = self._load_fc_credentials()
        # debug options are loaded here so that they don't appear in template
        if self.config.debug:
            self.reinstall = self.config.debug.reinstall
            self.nodeps = self.config.debug.nodeps
            self.timeout = self.config.debug.timeout
            self.vmonly = self.config.debug.vmonly
        else:
            debug = DebugConfig()
            self.reinstall = debug.reinstall
            self.nodeps = debug.nodeps
            self.timeout = debug.timeout
            self.vmonly = debug.vmonly


    def _load_config(self, path: Path) -> GeneralConfig:
        """
        Load config from toml file with pydantic validation.
        
        :param path: Path to toml config file
        :return: validated GeneralConfig instance
        """
        with path.open("rb") as f:
            conf = tomllib.load(f)
        return GeneralConfig.model_validate(conf)
    


    @staticmethod
    def write_template(path: Path = Path("config_template.toml")) -> None:
        """
        Write a template config file to the specified path.

        :param path: Path to the template config file
        """
        log(f"Writing config template to {path}...")
        cfg = GeneralConfig()
        with path.open("wb") as f:
            tomli_w.dump(cfg.model_dump(exclude_none=True), f)



    def _construct_client_strings(self) -> list[str]:
        """
        Generate strings for ssh connection to remote clients. 
        I.e. "user@hostname:port"

        :return: list of client connection strings
        """
        client_strings = []
        for cinfo in self.config.clients:
            cstr = f"{cinfo.username}@{cinfo.hostname}"
            if cinfo.port:
                cstr += f":{cinfo.port}"
            client_strings.append(cstr)
        log(f"client strings: {client_strings}")
        return client_strings

    

    def _load_fc_credentials(self) -> dict[str, str]:
        """
        Load the Featurecloud credentials of all clients from an environment file.

        :return: dictionary of Featurecloud credentials
        """
        load_dotenv(dotenv_path='.env', override=True)
        load_dotenv(dotenv_path='tests/env', override=True)
        fc_cred = {}
        for fc_user in self.fc_users:
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
        sshkeys = [c.sshkey for c in self.config.clients]
        self.serialg = SerialGroup(*client_strings, connect_kwargs={"key_filename": sshkeys})
        self.threadg = ThreadingGroup(*client_strings, connect_kwargs={"key_filename": sshkeys})
        log(f"serial group: {self.serialg}")
        return self.serialg, self.threadg


    
