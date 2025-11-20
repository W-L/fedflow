import tarfile
import shlex
from typing import Iterable
from pathlib import Path
import logging

from fabric import Connection

from logger import log
from utils import execute_fabric




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

