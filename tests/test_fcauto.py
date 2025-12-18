from fedsim import fcauto


def test_list_apps(capfd):
    fcauto.main(["list-apps"])
    captured = capfd.readouterr()
    assert "mean-app" in captured.err



def test_query_project(capfd):
    # requires FC credentials in env
    fcauto.main(["query", "-u", "federated.client+00@gmail.com", "-p", "17304"])
    captured = capfd.readouterr()
    assert "logged in: True" in captured.err
    assert "Project status:" in captured.err
    
