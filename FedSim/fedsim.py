from fabric import SerialGroup

from FedSim.utils import execute, construct_client_strings
from FedSim.vm_interaction import check_remotato_online
from FedSim.fabric_utils import launch_featurecloud, stop_featurecloud

# this is to orchestrate the entire simulated workflow

config = "resources/config_svd.toml"
clients = construct_client_strings(config=config)

# start up vms  

# check that the remotato services are online on all VMs
if check_remotato_online():
    print("All Remotato services are online.")


# install python venv on each VM   in provisioning first, then here, then back to provisioning
# playwright needs some dependencies that need sudo to install, so it's all back in there
# TODO: stopped here
# this is moved out of the provisioning to have more flexibility
# the installation of playwright does not work because its missing dependencies
# i put those into the common dependencies.sh script but it still didn't work
# clients = clients[:1]  
# for cxn in SerialGroup(*clients):
#     cxn.put('VMs/install_python_venv.sh', remote='/home/user/install_python_venv.sh')
#     cxn.put('VMs/requirements.txt', remote='/home/user/requirements.txt')
#     python_env = cxn.run('bash install_python_venv.sh')



# prep the environment on each VM - this should work
print('Transferring data and credentials to VMs...')
prep = 'python FedSim/prep_environment.py -c resources/config_svd.toml -e resources/.env'
stdout, stderr = execute(prep)
print(stderr)
print(stdout)

# run featurecloud controller on each VM - this didn't work because of docker inside docker
print('Starting FeatureCloud controllers on VMs...')

for cxn in SerialGroup(*clients):
    launch_featurecloud(conn=cxn)


for cxn in SerialGroup(*clients):
    stop_featurecloud(conn=cxn)



# start workflow as coordinator


# participate with all other clients

# check that the workflow ran successfully on all clients

# clean up

# shut down vms




# TODO 
# implement steps
# add arg to swap out VMs and containers
# add arg for real run?

