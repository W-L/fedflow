
from fabric import Connection

from utils import execute_fabric
from fabric_utils import transfer_with_packing, upload_file, write_to_file_remote
from logger import log



class Clients:

    """
    A wrapper around fabric.SerialGroup to manage client connections.
    """

    def __init__(self, serialgroup, conf):
        self.nodes = serialgroup
        self.conf = conf
        self.fcm = FCManager()


    def ping(self):
        for cxn in self.nodes:
            try:
               cmd = 'echo "Ping from $(hostname)"'
               _ = execute_fabric(cmd, cxn)
            except Exception as e:
                log(f"Error during ping of {cxn.host}: {e}")
        return



    def distribute_data(self) -> None:
        for cxn, data_paths in zip(self.nodes, self.conf.data_paths):
            transfer_with_packing(conn=cxn, paths=data_paths, remote_dir=self.conf.target_dir)
            upload_file(
                conn=cxn,
                local_path=self.conf.toml_path,
                remote_path=f"{self.conf.target_dir}/config.toml",
                force=True
            )


    def distribute_credentials(self) -> None:
        for cxn, (fc_user, fc_pass) in zip(self.nodes, self.conf.fc_creds.items()):            
            write_to_file_remote(
                conn=cxn,
                remote_path=f"{self.conf.target_dir}/.env",
                content=f"{fc_user}={fc_pass}\n"
            )



    def test_featurecloud_controllers(self):        
        for cxn in self.nodes:
            self.fcm.launch_featurecloud(conn=cxn)
            self.fcm.stop_featurecloud(conn=cxn)
        return


    def start_featurecloud_controllers(self):
        for cxn in self.nodes:
            self.fcm.launch_featurecloud(conn=cxn)
        return
    

    def stop_featurecloud_controllers(self):
        for cxn in self.nodes:
            self.fcm.stop_featurecloud(conn=cxn)
        return



class FCManager:

    def launch_featurecloud(self, conn: Connection):
        # launch featurecloud controller
        self.stop_featurecloud(conn=conn)  # ensure stopped before starting
        cmd = "source .venv/bin/activate && featurecloud controller start"
        stdout, stderr = execute_fabric(command=cmd, cxn=conn)
        self.check_featurecloud_status(conn=conn)

    def check_featurecloud_status(self, conn: Connection):
        # check featurecloud status
        cmd = "source .venv/bin/activate && featurecloud controller status"
        stdout, stderr = execute_fabric(command=cmd, cxn=conn)
        assert "running" in str(stdout).lower(), "FeatureCloud controller is not running."

    def stop_featurecloud(self, conn: Connection):
        # stop featurecloud controller
        cmd = "source .venv/bin/activate && featurecloud controller stop"
        stdout, stderr = execute_fabric(command=cmd, cxn=conn)
        



    
