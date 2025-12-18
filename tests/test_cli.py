import pytest
import fedsim.cli
from tests.constants import TOML_MEAN_TRIO, TOML_MEAN_TRIO_INT


def test_setup_run():
    conf = fedsim.cli.setup_run(config=TOML_MEAN_TRIO, log_mode="debug")
    assert conf is not None
    assert conf.config['general']['sim'] is True
    assert conf.config['general']['tool'] == "mean-app"
    assert len(conf.config['clients']) == 3



@pytest.mark.integration
def test_main():
    args = ["--config", TOML_MEAN_TRIO_INT, "--verbose"]
    fedsim.cli.main(argv=args)


