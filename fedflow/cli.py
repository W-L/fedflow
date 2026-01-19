import argparse
from datetime import datetime
from pathlib import Path
from time import sleep
import sys

from fedflow.logger import setup_logging, log
from fedflow.config import Config
from fedflow.VagrantManager import VagrantManager
from fedflow.ClientManager import ClientManager
from fedflow.provision import write_provision_script



def get_args(argv=None) -> argparse.Namespace:
     parser = argparse.ArgumentParser(description="Federated FeatureCloud.ai workflows on remote machines")
     group = parser.add_mutually_exclusive_group(required=True)
     group.add_argument("-c", "--config", help="Path to the config file")
     group.add_argument("-t", "--template", help="Generate template config", action="store_true", default=False)
     args = parser.parse_args(argv)
     return args



def get_client_connections(conf: Config):
    if not conf.config.sim:
        # construct connection group from config
        log('Connecting to remote clients defined in config...')
        serialg, threadg = conf.construct_connection_group()
    else:
        # construct connection group from vagrant
        log('Setting up Vagrant VMs...')
        nnodes = len(conf.config.clients)
        vms = VagrantManager(num_nodes=nnodes)
        vms.launch()
        serialg, threadg = vms.construct_connection_group()
    # set up wrapper for group of clients
    log("Setting up Fabric clients...")
    clients = ClientManager(serialg=serialg, threadg=threadg, clients=conf.config.clients)
    clients.ping()
    return clients


def prep_clients(clients: ClientManager, conf: Config):
    log("Provisioning...")
    clients.run_bash_script(script_path=write_provision_script())
    log("Resetting clients...")
    clients.reset_clients()
    log("Distributing credentials to clients...")
    clients.distribute_credentials(fc_creds=conf.fc_creds)
    log("Distributing data to clients...")
    clients.distribute_data()
    log("Installing fedflow package on clients...")
    clients.install_package(reinstall=conf.reinstall, nodeps=conf.nodeps)
    log("Starting FeatureCloud controllers on clients...")
    clients.start_featurecloud_controllers()


def prep_project(clients: ClientManager, conf: Config) -> str:
    project_id = None
    # attach featurecloud project
    if conf.config.project_id:
        # attach to existing project
        return str(conf.config.project_id)
    elif conf.config.tool:
        # create and join new project - serially
        log("Creating and joining FeatureCloud project...")
        project_id = clients.create_and_join_project(tool=conf.config.tool)
        return str(project_id)
    else:
        raise ValueError("Either project_id or tool must be specified in the config.")
    


def run_project(clients: ClientManager, project_id: str, timeout: int, outdir: str):
    # contribute data to project
    # once all participants have contributed, the project is started
    log("Contributing data to FeatureCloud project...")
    clients.contribute_data_to_project(project_id=project_id)
    # monitor run, then download logs and results
    log("Monitoring FeatureCloud project run...")
    clients.monitor_project_run(coordinator=clients.coordinator, project_id=project_id, timeout=timeout)
    sleep(10)
    # download outcome from all clients
    clients.fetch_results(outdir=outdir, pid=project_id)


def cleanup(clients: ClientManager, conf: Config):
    # stop fc controller and vms
    clients.stop_featurecloud_controllers()
    if conf.config.sim:
        log("Suspending Vagrant VMs...")
        # VagrantManager.suspend()


def main(argv=None):
    # parse arguments
    args = get_args(argv=argv)

    # print template config and exit
    if args.template:
        Config.write_template()
        sys.exit(0)

     # set up logging
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    setup_logging(f'{stamp}_fedflow.log')
    # load config
    log(f'Loading configuration from {args.config}...')
    conf = Config(toml=args.config)
    # set up fabric connections to all clients
    clients = get_client_connections(conf=conf)
    if conf.vmonly:
        log("Vagrant VMs launched. Exiting.")
        return
    # provision, reset, distribute creds and data, install fedflow, start fc controllers
    prep_clients(clients=clients, conf=conf)
    # get or create featurecloud project
    project_id = prep_project(clients=clients, conf=conf)
    # contribute data, monitor run, download results
    run_project(
        clients=clients,
        project_id=project_id,
        timeout=conf.timeout,
        outdir=conf.config.outdir
    )
    # stop fc controllers, halt vagrant vms
    cleanup(clients=clients, conf=conf)


if __name__ == "__main__":
    main()


