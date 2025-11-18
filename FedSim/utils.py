#%%
from types import SimpleNamespace
import subprocess
import random
import string
import logging

from logger import log




def empty_file(path: str) -> None:
    """
    Create an empty file at the specified path.

    :param path: The path to the file.
    """
    with open(path, 'w'):
        pass
    return



def randstr(l: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choices(alphabet, k=l))


def execute(command: str):
    """
    Execute a command in a shell and return the stdout and stderr.

    :param command: The command to execute.
    :return: The stdout and stderr as a tuple.
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
    
    stdout, stderr = running.communicate()
    log(f"STDOUT: \n{stdout}\n", level=logging.DEBUG)
    if stderr.strip() != "":
        log(f"STDERR: \n{stderr}\n")
    return stdout, stderr
    

def execute_fabric(command: str, cxn, silent: bool = False):
    # silent switch to make sure we don't expose credentials in logs
    if not silent:
        log(f'[{cxn.host}] CMD {command}', level=logging.DEBUG)
    result = cxn.run(command, hide=True)
    if not silent:
        log(f'[{cxn.host}] STDOUT: {result.stdout}')
        if result.stderr.strip() != "":
            log(f'[{cxn.host}] STDERR: \n{result.stderr}\n')
        return result.stdout, result.stderr
    return None, None
    


#%%

# execute('vagrant --version')
# %%
