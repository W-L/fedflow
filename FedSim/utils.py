from types import SimpleNamespace
import subprocess

from fabric import SerialGroup
import rtoml




def read_toml_config(toml_path: str) -> dict:
    with open(toml_path, "r") as f:
        config = rtoml.load(f)
    return config



def empty_file(path: str) -> None:
    """
    Create an empty file at the specified path.

    :param path: The path to the file.
    """
    with open(path, 'w'):
        pass
    return



def init_logger(logfile: str, args: SimpleNamespace) -> None:
    """
    Initialize the logger with the given logfile and log the arguments.

    :param logfile: The path to the logfile.
    :param args: The arguments to log.
    """
    empty_file(logfile)
    import logging
    logging.basicConfig(format='%(asctime)s %(message)s',
                        level=logging.INFO,
                        handlers=[logging.FileHandler(f"{logfile}"), logging.StreamHandler()])

    logging.info("FedSim")
    # logging.info(f"{version('fedsim')}")
    logging.info('\n')
    for a, aval in args.__dict__.items():
        logging.info(f'{a} {aval}')
    logging.info('\n')



def execute(command: str) -> tuple[str, str]:
    """
    Execute a command in a shell and return the stdout and stderr.

    :param command: The command to execute.
    :return: The stdout and stderr as a tuple.
    """
    # create the unix process
    running = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               encoding='utf-8', shell=True)
    # run on a shell and wait until it finishes
    stdout, stderr = running.communicate()
    return stdout, stderr


def construct_client_strings(config: str) -> list[str]:
    """
    Construct client strings from the clients dictionary.

    :param clients: The clients dictionary.
    :return: A list of client strings.
    """
    clients = read_toml_config(config)['clients']
    remote_username = list(clients.values())[0]['username']
    port = list(clients.values())[0]['port']
    client_strings = []
    
    for cname, cinfo in clients.items():
        cstr = f"{remote_username}@{cinfo['hostname']}"
        if port is not None and port != '':
            cstr += f":{cinfo['port']}"
        client_strings.append(cstr)

    return client_strings



def construct_serialgroup(conf: str, sshkey: str = ''):
    # generate the client strings
    client_strings = construct_client_strings(config=conf)
    print(client_strings)

    if sshkey:
        serialg = SerialGroup(*client_strings, connect_kwargs={"key_filename": sshkey})
    else:
        serialg = SerialGroup(*client_strings)

    return serialg




def is_vagrant_up(expected_nodes: int) -> bool:
    vagrant_status = 'vagrant status | grep "running " | wc -l'
    stdout, stderr = execute(vagrant_status)
    assert not stderr, f"Error checking Vagrant status: {stderr}"
    count = int(stdout.strip())
    assert count == expected_nodes, f"Expected {expected_nodes} Vagrant machines running, found {count}"
    return True






