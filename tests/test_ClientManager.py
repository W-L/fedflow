import pytest

from fedflow.ClientManager import ClientManager



@pytest.fixture
def client_manager_nosim(config_mean_trio_nosim):
    conf = config_mean_trio_nosim
    conf.construct_connection_group()

    manager = ClientManager(
        serialg=conf.serialg,
        threadg=conf.threadg,
        clients=conf.config.clients,
    )
    return manager




def test_client_manager_initialization(client_manager_nosim):
    cm = client_manager_nosim
    assert cm is not None
    assert len(cm.participants) == 2
    assert len(cm.coordinator) == 1
    assert cm.coordinator[0]['fc_username'] == "USER0"
    assert cm.participants[0]['fc_username'] == "USER1"
    

