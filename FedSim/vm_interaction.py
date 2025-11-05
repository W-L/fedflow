from FedSim.utils import execute


def check_remotato_online() -> bool:
    check_remotato_c = 'docker ps | grep remotato-remotato | wc -l'
    stdout, stderr = execute(check_remotato_c)
    assert not stderr, f"Error checking Remotato status: {stderr}"
    count = int(stdout.strip())
    assert count == 3, f"Expected 3 Remotato containers running, found {count}"
    return True



