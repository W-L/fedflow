from types import SimpleNamespace
import subprocess

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

    client_strings = []
    for cname, cinfo in clients.items():
        cname = 'user'   # TODO for now they are all called user, not cname (client0 etc.)
        cstr = f"{cname}@{cinfo['hostname']}:{cinfo['port']}"
        client_strings.append(cstr)
    return client_strings


