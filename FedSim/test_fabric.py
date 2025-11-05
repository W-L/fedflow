from fabric import Connection, SerialGroup
from FedSim.utils import transfer_with_packing








conn = Connection('user@localhost:2222')

conn.put('VMs/common_dependencies.sh', remote='/home/user/common_dependencies.sh')
conn.run('bash common_dependencies.sh')


launch_featurecloud(conn=conn)


for cxn in SerialGroup('user@localhost:2222', 'user@localhost:2223'):
    transfer_with_packing(conn=cxn, paths=['data/client0.txt', 'data/testing.txt'], remote_dir='/home/user/target')



