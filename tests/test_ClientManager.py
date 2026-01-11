import pytest

from fedsim.ClientManager import ClientManager



@pytest.fixture
def client_manager_nosim(config_mean_trio_nosim):
    conf = config_mean_trio_nosim
    conf.construct_serialgroup()

    manager = ClientManager(
        serialg=conf.serialg,
        threadg=conf.threadg,
        clients=conf.config['clients'],
    )
    return manager




def test_client_manager_initialization(client_manager_nosim):
    cm = client_manager_nosim
    assert cm is not None
    assert len(cm.all) == 3
    assert cm.coordinator[0]['fc_username'] == "USER0"
    assert cm.participants[0]['fc_username'] == "USER1"
    

