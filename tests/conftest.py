import os
import pytest
from dotenv import load_dotenv

from fedflow.config import Config
from fedflow.VagrantManager import VagrantManager
from fedflow.ClientManager import ClientManager
from tests.constants import TOML_MEAN_TRIO, TOML_MEAN_TRIO_NOSIM, TEST_ENV_FILE



@pytest.fixture
def config_mean_trio() -> Config:
    conf = Config(toml=TOML_MEAN_TRIO)
    return conf


@pytest.fixture
def config_mean_trio_nosim() -> Config:
    conf = Config(toml=TOML_MEAN_TRIO_NOSIM)
    return conf


@pytest.fixture
def fc_creds() -> dict[str, str]:
    load_dotenv(dotenv_path=TEST_ENV_FILE, override=True)
    fc_creds = {}
    for fc_user in ["USER0", "USER1", "USER2"]:
        fc_pass = os.getenv(f"{fc_user}")
        fc_creds[fc_user] = fc_pass
    return fc_creds



@pytest.fixture
def vagrant_manager():    
    vm = VagrantManager(num_nodes=3)
    return vm

