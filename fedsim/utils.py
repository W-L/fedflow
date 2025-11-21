import subprocess
import random
import string
import logging

from fedsim.logger import log




def empty_file(path: str) -> None:
    """
    Create an empty file at the specified path.

    :param path: The path to the file.
    """
    with open(path, 'w'):
        pass
    return



def randstr(l: int = 16) -> str:
    """
    Generate random alphanum string of length l

    :param l: length of random string to generate, defaults to 16
    :return: random alphanum 
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choices(alphabet, k=l))



def execute(command: str):
    """
    Execute a command in a shell and return the stdout and stderr.

    :param command: The command to execute.
    :return: stdout and stderr as a tuple.
    """
    log(f"CMD: {command}", level=logging.DEBUG)
    # create the unix process
    running = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,                
        encoding='utf-8',
        shell=True,
    )
    # wait for process to finish and log
    stdout, stderr = running.communicate()
    log(f"STDOUT: \n{stdout}\n", level=logging.DEBUG)
    if stderr.strip() != "":
        log(f"STDERR: \n{stderr}\n")
    return stdout, stderr
    


def execute_fabric(command: str, cxn, silent: bool = False):
    """
    Execute a command on a remote host using Fabric.

    :param command: Command to execute on remote
    :param cxn: fabric Connection instance to connect to
    :param silent: do not show any details of command or outputs
    :return: tuple stdout and stderr, or None
    """
    if not silent:
        log(f'[{cxn.host}] CMD {command}', level=logging.DEBUG)
    result = cxn.run(command, hide=True)
    if not silent:
        log(f'[{cxn.host}] STDOUT: {result.stdout}')
        if result.stderr.strip() != "":
            log(f'[{cxn.host}] STDERR: \n{result.stderr}\n')
        return result.stdout, result.stderr
    return None, None
    
