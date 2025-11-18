from logger import setup_logging, log
from config import Config
from utils_vm import VagrantManager
from clients import Clients



# STEP load config
CONFIG = "configs/config_svd_solo.toml"


setup_logging('fedsim.log', mode='quiet')
log(f'Loading configuration from {CONFIG}...')
conf = Config(toml_path=CONFIG)



# STEP get client connections
if not conf.config['general']['sim']:
    # construct serialgroup from config
    log('Connecting to remote clients defined in config...')
    serialgroup = conf.construct_serialgroup()
else:
    # construct serialgroup from vagrant
    log('Setting up Vagrant VMs...')
    nnodes = len(conf.config['clients'])
    # nnodes = 2  # TODO debug
    vms = VagrantManager(num_nodes=nnodes)
    vms.launch()
    serialgroup = vms.construct_serialgroup()


# STEP set up fabric clients
log("Setting up Fabric clients...")
clients = Clients(serialgroup=serialgroup, clients=conf.config['clients'])
clients.ping(nodes=clients.all)


# STEP copy data and credentials to each client
log("Distributing credentials to clients...")
clients.distribute_credentials(nodes=clients.all, fc_creds=conf.fc_creds)
log("Distributing data to clients...")
clients.distribute_data(nodes=clients.all)


# STEP launch featurecloud controller on each client
log("Launching FeatureCloud controllers on clients...")
# clients.test_featurecloud_controllers(nodes=clients.all)
clients.start_featurecloud_controllers(nodes=clients.all)
# clients.stop_featurecloud_controllers(nodes=clients.all)



# STEP attach featurecloud project
if 'project_id' in conf.config['general']:
    # attach to existing project
    project_id = conf.config['general']['project_id']
else:
    # create and join new project
    log("Creating and joining FeatureCloud project...")
    project_id = clients.create_and_join_project(
        coordinator=clients.coordinator,
        participants=clients.participants,
        tool="federated-svd"
    )



# STEP contribute data to project - this triggers the start of the workflow
log("Contributing data to FeatureCloud project...")
clients.contribute_data_to_project(nodes=clients.all, project_id=project_id)

# STEP monitor run and download logs and results
log("Monitoring FeatureCloud project run...")
clients.monitor_project_run(coordinator=clients.coordinator, project_id=project_id)



# STEP clean up
# TODO delete everything on the remotes
# stop fc controller and vms
# clients.stop_featurecloud_controllers(nodes=clients.all)
# if conf.config['general']['sim']:
    # log("Halting Vagrant VMs...")
    # vms.stop()


