import subprocess
import random
import string
import logging

from fedflow.logger import log



def randstr(l: int = 16) -> str:  # noqa: E741
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
    log(f"STDOUT: \n{stdout}", level=logging.DEBUG)
    if stderr.strip() != "":
        log(f"STDERR: \n{stderr}")
    return stdout, stderr
    

