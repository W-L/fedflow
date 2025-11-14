
from FedSim.utils import execute

from FedSim.fabric_utils import launch_featurecloud, stop_featurecloud

# this is to orchestrate the entire simulated workflow

CONFIG = "resources/config_svd_solo.toml"
SSHKEY = ".vagrant/machines/node-0/libvirt/private_key"


# TODO: write a log file here with all outputs and errors


# prep the environment on each VM - this should work
print('Transferring data and credentials to VMs...')
prep = f'python FedSim/prep_environment.py -c {CONFIG} -e resources/.env -i {SSHKEY}'
stdout, stderr = execute(prep)
print(stderr)
print(stdout)



# TODO: launching, status, and stopping fc on remote works as well!
# tested with test_remote_featurecloud.py
print('test fc...')
fc = f'python FedSim/test_remote_featurecloud.py -c {CONFIG} -i {SSHKEY}'
stdout, stderr = execute(fc)
print(stderr)
print(stdout)



# run featurecloud controller on each VM - this didn't work because of docker inside docker
# print('Starting FeatureCloud controllers on VMs...')

# for cxn in SerialGroup(*clients):
    # launch_featurecloud(conn=cxn)


# for cxn in SerialGroup(*clients):
    # stop_featurecloud(conn=cxn)



# start workflow as coordinator


# participate with all other clients

# check that the workflow ran successfully on all clients

# clean up

# shut down vms




# TODO 
# implement steps
# add arg to swap out VMs and containers
# add arg for real run?

