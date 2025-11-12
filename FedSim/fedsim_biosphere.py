

from FedSim.utils import execute

from FedSim.fabric_utils import launch_featurecloud, stop_featurecloud

# this is to orchestrate the entire simulated workflow

CONFIG = "resources/config_svd_solo.toml"
SSHKEY = "/home/lweilguny/.ssh/biosphere"
PROVISION_SCRIPT = "biosphere_provision.sh"


# TODO: write a log file here with all outputs and errors


# Provisioning via fabric on generic VMs without vagrant
print('Provision VMs...')
provision = f'python FedSim/provision_environment.py -c {CONFIG} -i {SSHKEY} -p {PROVISION_SCRIPT}'
stdout, stderr = execute(provision)
print(stderr)
print(stdout)   



# prep the environment on each VM - this should work
print('Transferring data and credentials to VMs...')
prep = f'python FedSim/prep_environment.py -c {CONFIG} -e resources/.env -i {SSHKEY}'
stdout, stderr = execute(prep)
print(stderr)
print(stdout)



# TODO: launching, status, and stopping fc on remote works as well!
# tested with test_remote_featurecloud.py



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

