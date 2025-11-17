#%%

from logger import setup_logging, log


from config import Config

from utils_vm import VagrantManager
from clients import Clients

%cd /home/lweilguny/FedSim

#%%



# STEP load config
CONFIG = "resources/config_svd_solo.toml"

setup_logging('fedsim.log')
log(f'Loading configuration from {CONFIG}...')
conf = Config(toml_path=CONFIG)
#%%



# STEP set up Vagrant VMs  (OPTIONAL if not using VMS)
log('Setting up Vagrant VMs...')
vms = VagrantManager(num_nodes=2)
vms.launch()
#%%


# STEP get client connections
if not conf.general['sim']:
    # construct serialgroup from config
    serialgroup = conf.construct_serialgroup()
else:
    # construct serialgroup from vagrant
    serialgroup = vms.construct_serialgroup()

clients = Clients(serialgroup=serialgroup, conf=conf)
# clients.ping()
#%%


# STEP copy data and credentials to each client
clients.distribute_credentials()
clients.distribute_data()
#%%


# TODO continue here with testing the logger
# and with the project creation api


# STEP test featurecloud
clients.test_featurecloud_controllers()
# clients.start_featurecloud_controllers()
# clients.stop_featurecloud_controllers()
#%%






# STEP use API


# create project and workflow as coordinator


# start workflow as coordinator
# participate with all other clients
# check that the workflow ran successfully on all clients

# clean up
# shut down vms



