import argparse
from datetime import datetime
from time import sleep

from fedsim.logger import setup_logging, log
from fedsim.config import Config
from fedsim.VagrantManager import VagrantManager
from fedsim.ClientManager import ClientManager



def get_args(argv=None) -> argparse.Namespace:
     parser = argparse.ArgumentParser(description="Simulated federated analyses with VMs")
     parser.add_argument("-c", "--config", help="Path to the config file", required=True)
     parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
     args = parser.parse_args(argv)
     return args



def setup_run(config: str, log_mode: str) -> Config:
    # set up logging
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    setup_logging(f'{stamp}_fedsim.log', mode=log_mode)
    # load config
    log(f'Loading configuration from {config}...')
    conf = Config(toml_path=config)
    return conf


def get_client_connections(conf: Config):
    if not conf.is_simulated:
        # construct serialgroup from config
        log('Connecting to remote clients defined in config...')
        serialgroup = conf.construct_serialgroup()
    else:
        # construct serialgroup from vagrant
        log('Setting up Vagrant VMs...')
        nnodes = len(conf.config['clients'])
        vms = VagrantManager(num_nodes=nnodes, provision_script=conf.provision_script)
        vms.launch()
        serialgroup = vms.construct_serialgroup()
    # use serialgroup to set up fabric clients
    log("Setting up Fabric clients...")
    clients = ClientManager(serialgroup=serialgroup, clients=conf.config['clients'])
    clients.ping(nodes=clients.all)
    return clients


def prep_clients(clients: ClientManager, conf: Config, project_id: str):
    # provision non-vagrant clients
    if not conf.is_simulated:
        log("Provisioning non-Vagrant clients...")
        clients.run_bash_script(script_path=conf.provision_script)
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
    # clients.test_featurecloud_controllers()
    # clients.stop_featurecloud_controllers()



def prep_project(clients: ClientManager, conf: Config) -> str:
    # attach featurecloud project
    if 'project_id' in conf.config['general']:
        # attach to existing project
        project_id = conf.config['general']['project_id']
    else:
        # create and join new project
        log("Creating and joining FeatureCloud project...")
        project_id = clients.create_and_join_project(
            coordinator=clients.coordinator,
            participants=clients.participants,
            tool=conf.config['general']['tool'],
        )
    return project_id


def run_project(clients: ClientManager, project_id: str, timeout: int, outdir: str):
    # contribute data to project
    # once all participants have contributed, the project is started
    log("Contributing data to FeatureCloud project...")
    clients.contribute_data_to_project(nodes=clients.all, project_id=project_id)
    # monitor run, then download logs and results
    log("Monitoring FeatureCloud project run...")
    clients.monitor_project_run(coordinator=clients.coordinator, project_id=project_id, timeout=timeout)
    sleep(10)
    # download outcome from all clients
    clients.fetch_results(outdir=outdir)



def cleanup(clients: ClientManager, conf: Config):
    # stop fc controller and vms
    clients.stop_featurecloud_controllers(nodes=clients.all)
    if conf.config['general']['sim']:
        log("Halting Vagrant VMs...")
        # VagrantManager.stop()
    pass


def main(argv=None):
    # parse arguments
    args = get_args(argv=argv)
    log_mode = "debug" if args.verbose else "quiet"
    # initialise logging and parse config file
    conf = setup_run(config=args.config, log_mode=log_mode)
    # set up fabric connections to all clients
    clients = get_client_connections(conf=conf)
    if conf.debug.vmonly:
        log("Vagrant VMs launched. Exiting.")
        return
    # get or create featurecloud project
    project_id = prep_project(clients=clients, conf=conf)
    # provision (if not vagrant), reset, distribute creds and data, install fedsim, start fc controllers
    prep_clients(clients=clients, conf=conf, project_id=project_id)
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


