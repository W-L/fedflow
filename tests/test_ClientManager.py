import pytest



@pytest.fixture
def fake_client_manager(config_mean_trio_nosim):
    from fedsim.ClientManager import ClientManager
    conf = config_mean_trio_nosim
    conf.construct_serialgroup()

    manager = ClientManager(
        serialgroup=conf.serialg,
        clients=conf.config['clients'],
    )

    return manager



def test_client_manager_initialization(fake_client_manager):
    cm = fake_client_manager
    assert cm is not None
    assert len(cm.all) == 3
    assert cm.coordinator[0]['fc_username'] == "USER0"
    assert cm.participants[0]['fc_username'] == "USER1"
    

