import tarfile
import shlex
from typing import Iterable
from pathlib import Path


from fabric import Connection



def test_fabric_connection(conn: Connection, hostname: str, username: str) -> None:
    """
    Test the fabric connection 

    :param conn: The fabric Connection object.
    """
    uname_result = conn.run('uname', hide=True).stdout.strip()
    assert uname_result != "", "Failed to get remote system info."
    username_result = conn.run('whoami', hide=True).stdout.strip()
    assert username_result == username, f"username {username_result} does not match expected {username}"
    # hostname_result = conn.run('hostname', hide=True).stdout.strip()
    # assert hostname_result == hostname, f"hostname {hostname_result} does not match expected {hostname}"
    return



def tarzip(paths: Iterable[str], archive_name: str, force: bool = False) -> None:
    """
    Create a gzipped tar archive from `paths`.
    """
    # check that archive does not already exist
    ap = Path(archive_name)
    
    if ap.exists():
        if not force:
            print(f"{archive_name} already exists. Skipping creation.")
            return 
    
    # create gzipped tar
    with tarfile.open(ap, "w:gz") as tar:
        for p in paths:
            tar.add(p, arcname=Path(p).name)
    print(f"Created archive {archive_name}.")
    return 



def upload_file(conn: Connection, local_path: str, remote_path: str, force: bool = False) -> None:
    """
    Upload a file to the remote via `conn`.

    - conn: fabric Connection to the remote host
    - local_path: path to the local file
    - remote_path: target path on the remote host
    """
    # check whether file exists remotely
    if conn.run(f"test -e {remote_path}", warn=True).ok:
        if not force:
            print(f"{remote_path} already exists on remote. Skipping upload.")
            return
    
    conn.run('mkdir -p ' + str(Path(remote_path).parent))
    print(f"Transferring {local_path} to remote...")
    conn.put(local_path, remote=remote_path)
    print("done.")
 


def remote_unpack(conn: Connection, remote_dir: str, remote_archive: str, remove_archive: bool = False) -> None:
    # extract on remote and remove archive
    r = conn.run(f"tar -xzf {remote_dir}/{remote_archive} -C {remote_dir}")
    assert r.ok, f"Remote extraction failed: {r.stderr}"
    print("Remote extraction done.")
    if remove_archive:
        conn.run(f"rm -f {remote_dir}/{remote_archive}")



def transfer_with_packing(conn: Connection, paths: Iterable[str], remote_dir: str) -> None:
    """
    Create a gzipped tar archive from `paths`, upload it to the remote via `conn`,
    unpack it into `remote_dir`, and remove the remote archive.

    - paths: iterable of file or directory paths on the local machine
    - conn: fabric Connection to the remote host
    - remote_dir: target directory on the remote to extract into (will be created)
    - archive_name: optional archive filename (defaults to files_<ts>.tar.gz)

    Example:
        transfer_with_packing(conn, ['data/file1.csv', 'data/subdir'], '/home/user/target')
    """
    # zip up files
    archive_name = 'destination_remote.tar.gz'
    tarzip(paths=paths, archive_name=archive_name, force=True)
    # transfer to remote
    upload_file(conn=conn, local_path=archive_name, remote_path=f"{remote_dir}/{archive_name}", force=True)
    # unpack on remote
    remote_unpack(conn=conn, remote_dir=remote_dir, remote_archive=archive_name, remove_archive=True)



def write_to_file_remote(conn: Connection, remote_path: str, content: str) -> None:
    """
    Write content to a file on the remote host via `conn`.

    :param conn: fabric Connection to the remote host
    :param remote_path: path to the file on the remote host
    :param content: content to write to the file
    """
    try:
        mkdirres = conn.run(f'mkdir -p {str(Path(remote_path).parent)}', hide=True)
        writeres = conn.run(f'echo {shlex.quote(content)} > {remote_path}', hide=True)
    except Exception as e:
        print(f"Error writing to {remote_path}: {e}")
    return


def launch_featurecloud(conn: Connection):
    # launch featurecloud controller
    stop_featurecloud(conn=conn)  # ensure stopped before starting
    fc_res = conn.run("source .venv/bin/activate && featurecloud controller start")
    print(fc_res.stdout)
    check_featurecloud_status(conn=conn)


def check_featurecloud_status(conn: Connection):
    # check featurecloud status
    status_res = conn.run("source .venv/bin/activate && featurecloud controller status")
    print(status_res.stdout)
    assert "running" in status_res.stdout.lower(), "FeatureCloud controller is not running."


def stop_featurecloud(conn: Connection):
    # stop featurecloud controller
    stop_res = conn.run("source .venv/bin/activate && featurecloud controller stop")
    print(stop_res.stdout)


    