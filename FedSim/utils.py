#%%
from types import SimpleNamespace
import subprocess
from logger import log




def empty_file(path: str) -> None:
    """
    Create an empty file at the specified path.

    :param path: The path to the file.
    """
    with open(path, 'w'):
        pass
    return





def execute(command: str):
    """
    Execute a command in a shell and return the stdout and stderr.

    :param command: The command to execute.
    :return: The stdout and stderr as a tuple.
    """
    log(f"CMD: {command}")
    # create the unix process
    running = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,                
        encoding='utf-8',
        shell=True,
    )
    
    stdout, stderr = running.communicate()
    log(f"STDOUT: \n{stdout}\n")
    if stderr.strip() != "":
        log(f"STDERR: \n{stderr}\n")
    return stdout, stderr
    

def execute_fabric(command: str, cxn, silent: bool = False):
    # silent switch to make sure we don't expose credentials in logs
    if not silent:
        log(f'[{cxn.host}] CMD {command}')
    result = cxn.run(command, hide=True)
    if not silent:
        log(f'[{cxn.host}] STDOUT: \n{result.stdout}\n')
        if result.stderr.strip() != "":
            log(f'[{cxn.host}] STDERR: \n{result.stderr}\n')
        return result.stdout, result.stderr
    return None, None
    


#%%

# execute('vagrant --version')
# %%
