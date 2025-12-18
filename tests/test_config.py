


def test_config(config_mean_trio, fc_creds):
    assert fc_creds["USER0"] == "PASS0"
    assert config_mean_trio.n == 3
    assert config_mean_trio.fc_users == ["USER0", "USER1", "USER2"]
    assert config_mean_trio.fc_creds == fc_creds
    

def test_construct_serialgroup(config_mean_trio_nosim):
    client_strings = config_mean_trio_nosim._construct_client_strings()
    expected_strings = [
        "user0@host0:00",
        "user1@host1:01",
        "user2@host2:02",
    ]
    assert client_strings == expected_strings
    serialg = config_mean_trio_nosim.construct_serialgroup()
    assert serialg is not None

