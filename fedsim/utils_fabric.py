import tarfile
import shlex
from typing import Iterable
from pathlib import Path
import logging

from fabric import Connection

from fedsim.logger import log
from fedsim.utils import execute_fabric




def tarzip(paths: Iterable[str], archive_name: str, force: bool = False) -> None:
    """
    Create a gzipped tar archive from `paths` for easy transfer.

    :param paths: Data to gzip and tar into an archive
    :param archive_name: name of the target archive
    :param force: whether to overwrite existing archive, defaults to False
    """
    # check that archive does not already exist
    ap = Path(archive_name)
    # only overwrite if force == True
    if ap.exists():
        if not force:
            log(f"{archive_name} already exists. Skipping creation.")
            return 
    # create gzipped tar
    with tarfile.open(ap, "w:gz") as tar:
        for p in paths:
            tar.add(p, arcname=Path(p).name)
    log(f"Created archive {archive_name}.", level=logging.DEBUG)
    return 



def upload_file(conn: Connection, local_path: str, remote_path: str, force: bool = False) -> None:
    """
    Upload a file to a fabric Connection. Wrapper around Connection.put()

    :param conn: fabric Connection to the remote host
    :param local_path: path of the local file to upload
    :param remote_path: remote target path
    :param force: whether to overwrite existing file, defaults to False
    """
    # check whether file exists remotely
    if conn.run(f"test -e {remote_path}", warn=True).ok:
        if not force:
            print(f"{remote_path} already exists on remote. Skipping upload.")
            return
    # ensure parent directory exists
    execute_fabric('mkdir -p ' + str(Path(remote_path).parent), cxn=conn, silent=True)
    log(f"Transferring {local_path} to remote...", level=logging.DEBUG)
    conn.put(local_path, remote=remote_path)
    log("done.", level=logging.DEBUG)
 


def remote_unpack(conn: Connection, remote_archive: str, remove_archive: bool = False) -> None:
    """
    Extract a gzipped tar archive on a fabric remote.

    :param conn: fabric Connection to the remote host
    :param remote_archive: path to the remote archive file
    :param remove_archive: whether to remove the archive after extraction, defaults to False
    """
    # extract on remote and remove archive
    log(f"Extracting {remote_archive} on remote...", level=logging.DEBUG)
    cmd = f"tar -xzf {remote_archive}"
    execute_fabric(command=cmd, cxn=conn)
    log("Remote extraction done.", level=logging.DEBUG)
    if remove_archive:
        conn.run(f"rm -f {remote_archive}")



def transfer_with_packing(conn: Connection, paths: Iterable[str]) -> None:
    """
    Transfer files to a remote host with packing.

    :param conn: Fabric Connection to the remote host
    :param paths: Iterable of file paths to transfer
    """
    # zip up files
    archive_name = 'destination_remote.tar.gz'
    tarzip(paths=paths, archive_name=archive_name, force=True)
    # transfer to remote
    upload_file(conn=conn, local_path=archive_name, remote_path=archive_name, force=True)
    # unpack on remote
    remote_unpack(conn=conn, remote_archive=archive_name, remove_archive=True)



def fetch_remote_dir(conn: Connection, remote_dir: str, local_dir: str | Path):
    """
    Download a remote directory by archiving it on the remote host,
    transferring the archive, extracting locally, and cleaning up.

    :param conn: fabric Connection to the remote host
    :param remote_dir: path to the remote directory to download
    :param local_dir: local directory to save the downloaded content
    """
    fcuser = conn["fc_username"]
    local_dir = Path(f"{local_dir}/{fcuser}")
    local_dir.mkdir(parents=True, exist_ok=True)

    remote_dir = remote_dir.rstrip("/")
    archive_name = Path(remote_dir).name + ".tar.gz"
    local_archive = local_dir / archive_name

    # Create archive remotely
    parent = str(Path(remote_dir).parent)
    base = Path(remote_dir).name
    conn.run(f"tar -czf {archive_name} -C {parent} {base}")
    # Transfer archive
    conn.get(archive_name, str(local_archive))
    # Extract locally
    with tarfile.open(local_archive, "r:gz") as tar:
        tar.extractall(local_dir)
    # cleanup
    conn.run(f"rm -f {archive_name}")
    local_archive.unlink()



def write_to_file_remote(conn: Connection, remote_path: str, content: str) -> None:
    """
    Write content to a file on the remote host via `conn`.

    :param conn: fabric Connection to the remote host
    :param remote_path: path to the file on the remote host
    :param content: content to write to the file
    """
    try:
        execute_fabric(f'mkdir -p {str(Path(remote_path).parent)}', cxn=conn, silent=True)
        execute_fabric(f'echo {shlex.quote(content)} > {remote_path}', cxn=conn, silent=True)
    except Exception as e:
        log(f"Error writing to {remote_path}: {e}")
    return



def launch_featurecloud(conn: Connection) -> None:
    """
    Launch the Featurecloud controller on a remote.

    :param conn: fabric Connection to the remote host
    """
    # launch featurecloud controller
    # ensure stopped before starting
    # this will also ensure that we have a fresh log file
    stop_featurecloud(conn=conn)  
    cmd = "source .venv/bin/activate && featurecloud controller start"
    stdout, stderr = execute_fabric(command=cmd, cxn=conn)
    assert is_controller_running(conn=conn), "Failed to start FeatureCloud controller"



def is_controller_running(conn: Connection) -> bool:
    """
    Check whether the Featurecloud controller is running on a remote.

    :param conn: fabric Connection to the remote host
    :return: boolean indicating whether the controller is running
    """
    cmd = "source .venv/bin/activate && featurecloud controller status"
    stdout, stderr = execute_fabric(command=cmd, cxn=conn)
    if "running" in str(stdout).lower():
        return True
    else:
        return False



def stop_featurecloud(conn: Connection) -> None:
    """
    Stop Featurecloud controller on a remote.

    :param conn: fabric Connection to the remote host
    """
    cmd = "source .venv/bin/activate && featurecloud controller stop"
    stdout, stderr = execute_fabric(command=cmd, cxn=conn)
         

