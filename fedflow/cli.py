import argparse
from datetime import datetime
from time import sleep

from fedflow.logger import setup_logging, log
from fedflow.config import Config
from fedflow.VagrantManager import VagrantManager
from fedflow.ClientManager import ClientManager
from fedflow.provision import write_provision_script



def get_args(argv=None) -> argparse.Namespace:
     parser = argparse.ArgumentParser(description="Simulated federated analyses with VMs")
     parser.add_argument("-c", "--config", help="Path to the config file", required=True)
     args = parser.parse_args(argv)
     return args


def setup_run(config: str) -> Config:
    # set up logging
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    setup_logging(f'{stamp}_fedsim.log')
    # load config
    log(f'Loading configuration from {config}...')
    conf = Config(toml_path=config)
    return conf


def get_client_connections(conf: Config):
    if not conf.is_simulated:
        # construct connection group from config
        log('Connecting to remote clients defined in config...')
        serialg, threadg = conf.construct_connection_group()
    else:
        # construct connection group from vagrant
        log('Setting up Vagrant VMs...')
        nnodes = len(conf.config['clients'])
        vms = VagrantManager(num_nodes=nnodes)
        vms.launch()
        serialg, threadg = vms.construct_connection_group()
    # set up wrapper for group of clients
    log("Setting up Fabric clients...")
    clients = ClientManager(serialg=serialg, threadg=threadg, clients=conf.config['clients'])
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
    log("Installing fedsim package on clients...")
    clients.install_package(reinstall=conf.debug.reinstall, nodeps=conf.debug.nodeps)
    log("Starting FeatureCloud controllers on clients...")
    clients.start_featurecloud_controllers()


def prep_project(clients: ClientManager, conf: Config) -> str:
    # attach featurecloud project
    if 'project_id' in conf.config['general']:
        # attach to existing project
        project_id = conf.config['general']['project_id']
    else:
        # create and join new project - serially
        log("Creating and joining FeatureCloud project...")
        project_id = clients.create_and_join_project(tool=conf.config['general']['tool'])
    return project_id


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
    if conf.is_simulated:
        log("Halting Vagrant VMs...")
        # VagrantManager.stop()


def main(argv=None):
    # parse arguments
    args = get_args(argv=argv)
    # initialise logging and parse config file
    conf = setup_run(config=args.config)
    # set up fabric connections to all clients
    clients = get_client_connections(conf=conf)
    if conf.debug.vmonly:
        log("Vagrant VMs launched. Exiting.")
        return
    # get or create featurecloud project
    project_id = prep_project(clients=clients, conf=conf)
    # provision, reset, distribute creds and data, install fedsim, start fc controllers
    prep_clients(clients=clients, conf=conf)
    # contribute data, monitor run, download results
    run_project(
        clients=clients,
        project_id=project_id,
        timeout=conf.debug.timeout,
        outdir=conf.outdir
    )
    # stop fc controllers, halt vagrant vms
    cleanup(clients=clients, conf=conf)


if __name__ == "__main__":
    main()


