from copy import deepcopy
from pathlib import Path
import argparse
from typing import Any

import rtoml
from pydantic import BaseModel, ConfigDict




def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate fedflow config from template")
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--app-config", type=str, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project-id", type=int, default=None)
    parser.add_argument("--provider", type=str, required=True)
    parser.add_argument("--tool", type=str, required=True)
    parser.add_argument("--mode", type=str, choices=["fed", "cent"], required=True)
    parser.add_argument("--rep", type=str, required=True)
    parser.add_argument("--accessions", type=str, nargs="+", required=True)
    parser.add_argument("--fc-usernames", type=str, nargs="+", required=True)
    parser.add_argument("--provider-username", type=str, default="")
    parser.add_argument("--provider-sshkey", type=str, default="")
    parser.add_argument("--hostnames", type=str, nargs="*", default=[])
    parser.add_argument("--debug-nodeps", action="store_true")
    return parser.parse_args()


class ClientConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    coordinator: bool = False
    fc_username: str
    data: list[str]
    hostname: str | None = None
    username: str | None = None
    sshkey: str | None = None


class FedflowConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    outdir: str
    project_id: int | None = None
    clients: list[ClientConfig]


def validate_config(config_data: dict[str, Any], provider: str) -> dict[str, Any]:
    validated = FedflowConfig.model_validate(config_data)
    if not validated.clients:
        raise ValueError("Generated config must contain at least one client")
    if not validated.clients[0].coordinator:
        raise ValueError("First client must be coordinator")

    if provider == "biosphere":
        for idx, cl in enumerate(validated.clients):
            if not cl.hostname or not cl.username or not cl.sshkey:
                raise ValueError(
                    f"biosphere client {idx} is missing hostname/username/sshkey"
                )

    return validated.model_dump(exclude_none=True)


def build_client_data(tool: str, mode: str, rep: str, accession: str, app_config: str) -> list[str]:
    # full data path 
    if mode == "fed":
        data_root = Path("data") / tool / mode / accession / rep
    elif mode == "cent":
        data_root = Path("data") / tool / mode / "P0" / rep
    else:
        raise ValueError(f"Invalid mode: {mode}")
    
    data_files = [str(data_root / "input.csv")]
    if tool == "random-forest":
        data_files.append(str(data_root / "input_test.csv"))

    data_files.append(app_config)
    return data_files


def build_clients(
    template_clients: list[dict],
    accessions: list[str],
    fc_usernames: list[str],
    provider: str,
    provider_config: dict,
    tool: str,
    mode: str,
    rep: str,
    app_config: str,
) -> list[dict]:
    expected_clients = len(accessions) if mode == "fed" else 1
    if not template_clients:
        raise ValueError("Template must contain at least one client entry")
    if len(fc_usernames) < expected_clients:
        raise ValueError(
            f"Only {len(fc_usernames)} fc_usernames provided, but {expected_clients} are required"
        )

    hostnames = provider_config.get("hostnames", [])
    if provider == "biosphere" and len(hostnames) < expected_clients:
        raise ValueError(
            f"Only {len(hostnames)} hostnames provided for biosphere, but {expected_clients} are required"
        )

    clients_out = []
    client_template = deepcopy(template_clients[0])

    for idx in range(expected_clients):
        client = deepcopy(client_template)
        client["coordinator"] = idx == 0
        client["fc_username"] = fc_usernames[idx]

        if provider == "biosphere":
            username = provider_config.get("username")
            sshkey = provider_config.get("sshkey")
            if not username or not sshkey:
                raise ValueError("biosphere provider requires username and sshkey")
            client["hostname"] = hostnames[idx]
            client["username"] = username
            client["sshkey"] = sshkey
        else:
            # Keep non-SSH providers clean and driven by their template defaults.
            client.pop("hostname", None)
            client.pop("username", None)
            client.pop("sshkey", None)

        accession = accessions[idx] 
        client["data"] = build_client_data(
            tool=tool,
            mode=mode,
            rep=rep,
            accession=accession,
            app_config=app_config,
        )
        clients_out.append(client)

    return clients_out


def main() -> None:
    args = get_args()

    with args.template.open("r") as f:
        template = rtoml.load(f)

    accessions = args.accessions
    fc_usernames = args.fc_usernames
    provider_config = {
        "username": args.provider_username,
        "sshkey": args.provider_sshkey,
        "hostnames": args.hostnames,
    }

    template["outdir"] = f"results/{args.provider}/{args.tool}/{args.mode}/{args.rep}/"
    template["project_id"] = args.project_id if args.project_id is not None else template.get("project_id", None)
    if args.debug_nodeps:
        debug_config = template.get("debug", {})
        debug_config["nodeps"] = True
        template["debug"] = debug_config
    template["clients"] = build_clients(
        template_clients=template.get("clients", []),
        accessions=accessions,
        fc_usernames=fc_usernames,
        provider=args.provider,
        provider_config=provider_config,
        tool=args.tool,
        mode=args.mode,
        rep=args.rep,
        app_config=args.app_config,
    )

    template = validate_config(template, provider=args.provider)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as f:
        rtoml.dump(template, f)


if __name__ == "__main__":
    main()
