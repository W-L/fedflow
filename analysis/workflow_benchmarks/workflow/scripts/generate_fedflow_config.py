import argparse
from copy import deepcopy
from pathlib import Path
import tomllib

import tomli_w  # type: ignore


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate fedflow config for mean-app benchmark")
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--app-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--outdir", type=str, required=True)
    parser.add_argument("--nclients", type=int, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--fc-usernames-file", type=Path, required=True)
    parser.add_argument("--username", type=str, default="")
    parser.add_argument("--sshkey", type=str, default="")
    parser.add_argument("--hostnames-file", type=Path, required=True)
    parser.add_argument("--project-id-file", type=Path, default=None)
    parser.add_argument("--debug-nodeps", action="store_true")
    return parser.parse_args()



def build_clients(args: argparse.Namespace, template_clients: list[dict]) -> list[dict]:
    with args.fc_usernames_file.open("r") as handle:
        fc_usernames = [line.strip() for line in handle if line.strip()]
    with args.hostnames_file.open("r") as handle:
        hostnames = [line.strip() for line in handle if line.strip()]

    client_template = deepcopy(template_clients[0])
    clients = []
    for client_index in range(args.nclients):
        client = deepcopy(client_template)
        client["coordinator"] = client_index == 0
        client["fc_username"] = fc_usernames[client_index]
        client["data"] = [
            str(args.data_root / f"client_{client_index}" / "data.csv"),
            str(args.app_config),
        ]
        client["hostname"] = hostnames[client_index]
        client["username"] = args.username
        client["sshkey"] = args.sshkey
        clients.append(client)
    return clients



if __name__ == "__main__":
    args = get_args()
    with args.template.open("rb") as handle:
        template = tomllib.load(handle)

    template["outdir"] = args.outdir
    if args.project_id_file is not None:
        with args.project_id_file.open("r", encoding="utf-8") as handle:
            project_id = int(handle.read().strip())
        template["project_id"] = project_id
    else:
        template.pop("project_id", None)

    debug = template.get("debug", {})
    ###
    # debug['reinstall'] = False
    # debug['nodeps'] = True
    # debug['wheel'] = '/home/lweilguny/fedflow/dist/fedflow_featurecloud-0.0.5-py3-none-any.whl'
    ###
    template["debug"] = debug
    template["clients"] = build_clients(args, template.get("clients", []))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("wb") as handle:
        tomli_w.dump(template, handle)

