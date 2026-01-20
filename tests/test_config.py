from fabric import SerialGroup, ThreadingGroup


def test_config(config_mean_trio, fc_creds):
    assert fc_creds["USER0"] == "PASS0"
    assert config_mean_trio.n == 3
    assert config_mean_trio.fc_users == ["USER0", "USER1", "USER2"]
    assert config_mean_trio.fc_creds == fc_creds
    

def test_construct_connection_group(config_mean_trio_nosim):
    client_strings = config_mean_trio_nosim._construct_client_strings()
    expected_strings = [
        "user0@host0:11",
        "user1@host1:22",
        "user2@host2:33",
    ]
    assert client_strings == expected_strings
    serialg, threadg = config_mean_trio_nosim.construct_connection_group()
    assert serialg is not None
    assert threadg is not None
    assert isinstance(serialg, SerialGroup)
    assert isinstance(threadg, ThreadingGroup)
