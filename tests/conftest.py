import os

import pytest
from dotenv import load_dotenv

from fedsim.config import Config


TOML_MEAN_TRIO = "tests/configs/config_mean_trio.toml" 
TOML_MEAN_TRIO_NOSIM = "tests/configs/config_mean_trio_nosim.toml" 
TEST_ENV_FILE = "tests/env"



@pytest.fixture
def config_mean_trio() -> Config:
    conf = Config(toml_path=TOML_MEAN_TRIO)
    return conf


@pytest.fixture
def config_mean_trio_nosim() -> Config:
    conf = Config(toml_path=TOML_MEAN_TRIO_NOSIM)
    return conf


@pytest.fixture
def fc_creds() -> dict[str, str]:
    load_dotenv(dotenv_path=TEST_ENV_FILE, override=True)
    fc_creds = {}
    for fc_user in ["USER0", "USER1", "USER2"]:
        fc_pass = os.getenv(f"{fc_user}")
        fc_creds[fc_user] = fc_pass
    return fc_creds





