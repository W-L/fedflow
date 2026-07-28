import argparse
from datetime import datetime
from time import sleep
import sys

from fedflow.logger import setup_logging, log
from fedflow.config import Config
from fedflow.VagrantManager import VagrantManager
from fedflow.ClientManager import ClientManager
from fedflow.metrics import MetricsRecorder
from fedflow.provision import write_provision_script



def get_args(argv=None) -> argparse.Namespace:
     parser = argparse.ArgumentParser(description="Federated FeatureCloud.ai workflows on remote machines")
     group = parser.add_mutually_exclusive_group(required=True)
     group.add_argument("-c", "--config", help="Path to the config file")
     group.add_argument("-t", "--template", help="Generate template config", action="store_true", default=False)
     args = parser.parse_args(argv)
     return args



def get_client_connections(conf: Config, metrics: MetricsRecorder):
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
    clients = ClientManager(serialg=serialg, threadg=threadg, clients=conf.config.clients, metrics=metrics)
    clients.ping()
    return clients


def prep_clients(clients: ClientManager, conf: Config, metrics: MetricsRecorder):
    log("Provisioning...")
    # either run user-supplied provision script or built-in 
    if conf.config.provision_script:
        script_path = conf.config.provision_script
    else:
        script_path = write_provision_script()
    with metrics.phase("provision_clients"):
        clients.run_bash_script(script_path=script_path)

    log("Resetting clients...")
    with metrics.phase("reset_clients"):
        clients.reset_clients()

    if not conf.config.skip_credential_transfer:
        log("Distributing credentials to clients...")
        with metrics.phase("distribute_credentials"):
            clients.distribute_credentials(fc_creds=conf.fc_creds)

    if not conf.config.skip_data_transfer:
        log("Distributing data to clients...")
        with metrics.phase("distribute_data"):
            clients.distribute_data()

    log("Installing fedflow package on clients...")
    with metrics.phase("install_package"):
        clients.install_package(wheel=conf.wheel, reinstall=conf.reinstall, nodeps=conf.nodeps)

    log("Starting FeatureCloud controllers on clients...")
    with metrics.phase("start_featurecloud_controllers"):
        clients.start_featurecloud_controllers()


def prep_project(clients: ClientManager, conf: Config) -> str:
    project_id = None
    # attach featurecloud project
    if conf.config.project_id:
        # attach to existing project
        project_id = str(conf.config.project_id)
    elif conf.config.tool:
        # create and join new project - serially
        log("Creating and joining FeatureCloud project...")
        project_id = clients.create_and_join_project(tool=conf.config.tool)
    else:
        raise ValueError("Either project_id or tool must be specified in the config.")
    # set project to prepare mode with the coordinator
    clients.set_project_to_prepare(coordinator=clients.coordinator, project_id=project_id)
    return project_id


def run_project(
    clients: ClientManager,
    project_id: str,
    timeout: int,
    outdir: str,
    skip_result_transfer: bool,
    metrics: MetricsRecorder,
):
    # contribute data to project
    # once all participants have contributed, the project is started
    log("Contributing data to FeatureCloud project...")
    with metrics.phase("contribute_data_to_project", project_id=project_id):
        clients.contribute_data_to_project(project_id=project_id)
    # monitor run, then download logs and results
    sleep(10)
    log("Monitoring FeatureCloud project run...")
    with metrics.phase("monitor_project_run", timeout=timeout):
        clients.monitor_project_run(coordinator=clients.coordinator, project_id=project_id, timeout=timeout)
    with metrics.phase("post_run_settle_sleep", seconds=5):
        sleep(5)
    if not skip_result_transfer:
        # download outcome from all clients
        with metrics.phase("fetch_results", project_id=project_id):
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
    log_path = f'{stamp}_fedflow.log'
    setup_logging(log_path)
    clients = None
    metrics = None
    status = "completed"
    error_message = None
    try:
        # load config
        log(f'Loading configuration from {args.config}...')
        conf = Config(toml=args.config)
        metrics = MetricsRecorder(config_path=args.config, outdir=conf.config.outdir, stamp=stamp, log_path=log_path)
        metrics.set_metadata("client_count", len(conf.config.clients))
        # set up fabric connections to all clients
        with metrics.phase("connect_clients"):
            clients = get_client_connections(conf=conf, metrics=metrics)
        if conf.vmonly:
            log("Vagrant VMs launched. Exiting.")
            return
        # provision, reset, distribute creds and data, install fedflow, start fc controllers
        prep_clients(clients=clients, conf=conf, metrics=metrics)
        # get or create featurecloud project
        with metrics.phase("create_and_join_project", tool=conf.config.tool):
            project_id = prep_project(clients=clients, conf=conf)
        metrics.set_metadata("project_id", project_id)
        # contribute data, monitor run, download results
        run_project(
            clients=clients,
            project_id=project_id,
            timeout=conf.timeout,
            outdir=conf.config.outdir,
            skip_result_transfer=conf.config.skip_result_transfer,
            metrics=metrics,
        )
        # stop fc controllers, halt vagrant vms
        with metrics.phase("cleanup"):
            cleanup(clients=clients, conf=conf)
    except Exception as exc:
        status = "failed"
        error_message = str(exc)
        raise
    finally:
        if metrics:
            metrics_path = metrics.write(status=status, error=error_message)
            log(f"Wrote run metrics to {metrics_path}")


if __name__ == "__main__":
    main()


