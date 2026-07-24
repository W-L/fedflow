import argparse
import fcntl
from pathlib import Path
import subprocess
import tempfile
import time



def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run fedflow with per-host lock files")
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--app-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--outdir", type=str, required=True)
    parser.add_argument("--nclients", type=int, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--fc-usernames-file", type=Path, required=True)
    parser.add_argument("--hostnames-file", type=Path, required=True)
    parser.add_argument("--username", type=str, default="")
    parser.add_argument("--sshkey", type=str, default="")
    return parser.parse_args()


def read_lines(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as handle:
        return [line.strip() for line in handle if line.strip()]


def acquire_host_locks(hostnames: list[str], nclients: int):
    lock_dir = Path('results/lock')
    lock_dir.mkdir(parents=True, exist_ok=True)

    while True:
        locked_indices = []
        lock_handles = []

        for host_index, hostname in enumerate(hostnames):
            lock_path = lock_dir / f"host_{host_index:04d}_{hostname}.lock"
            handle = lock_path.open("a+")
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                handle.close()
                continue

            locked_indices.append(host_index)
            lock_handles.append(handle)
            if len(locked_indices) == nclients:
                return locked_indices, lock_handles

        for handle in lock_handles:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()

        time.sleep(2)


def release_locks(lock_handles: list) -> None:
    for handle in lock_handles:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()



# prep hosts for this execution of fedflow
args = get_args()

with args.fc_usernames_file.open("r") as fh:
    fc_usernames = [line.strip() for line in fh if line.strip()]

with args.hostnames_file.open("r") as fh:
    hostnames = [line.strip() for line in fh if line.strip()]

# grab some free hosts and lock them in
selected_indices, lock_handles = acquire_host_locks(hostnames, args.nclients)

try:
    selected_usernames = [fc_usernames[i] for i in selected_indices]
    selected_hostnames = [hostnames[i] for i in selected_indices]

    with tempfile.TemporaryDirectory(prefix="fedflow-lockrun-") as tmpdir:
        tmpdir_path = Path(tmpdir)
        selected_users_file = tmpdir_path / "fc_usernames_selected.txt"
        selected_hosts_file = tmpdir_path / "hostnames_selected.txt"
        selected_users_text = "\n".join(selected_usernames) + "\n"
        selected_hosts_text = "\n".join(selected_hostnames) + "\n"
        selected_users_file.write_text(selected_users_text)
        selected_hosts_file.write_text(selected_hosts_text)
        print(selected_users_text)
        print(selected_hosts_text)

        cmd = [
            "python",
            "workflow/scripts/generate_fedflow_config.py",
            "--template", str(args.template),
            "--app-config", str(args.app_config),
            "--output", str(args.output),
            "--outdir", args.outdir,
            "--nclients", str(args.nclients),
            "--data-root", str(args.data_root),
            "--fc-usernames-file", str(selected_users_file),
            "--hostnames-file", str(selected_hosts_file),
            "--username", args.username,
            "--sshkey", args.sshkey,
        ]
        
        subprocess.run(cmd, check=True)
        subprocess.run(["fedflow", "-c", str(args.output)], check=True)
finally:
    release_locks(lock_handles)


