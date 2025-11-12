from fabric import Connection, SerialGroup
from FedSim.utils import transfer_with_packing








conn = Connection('user@localhost:2222')

conn.put('VMs/common_dependencies.sh', remote='/home/user/common_dependencies.sh')
conn.run('bash common_dependencies.sh')



conn = Connection('ubuntu@134.158.249.96', connect_kwargs={"key_filename": "/home/lweilguny/.ssh/biosphere"})
conn.put('VMs/biosphere_provision.sh', remote='/home/ubuntu/biosphere_provision.sh')



launch_featurecloud(conn=conn)


for cxn in SerialGroup('user@localhost:2222', 'user@localhost:2223'):
    transfer_with_packing(conn=cxn, paths=['data/client0.txt', 'data/testing.txt'], remote_dir='/home/user/target')



