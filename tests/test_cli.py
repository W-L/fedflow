import pytest
import fedflow.cli
from tests.constants import TOML_MEAN_TRIO_INT




@pytest.mark.integration
def test_main():
   args = ["--config", TOML_MEAN_TRIO_INT]
   fedflow.cli.main(argv=args)



def test_write_template():
   pass # TODO

