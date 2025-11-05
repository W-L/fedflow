from pathlib import Path
import os

from fabric import Connection

from FedSim.fabric_utils import write_to_file_remote, test_fabric_connection, transfer_with_packing, upload_file


class Client: 

    def __init__(self, name: str, info: dict, target_dir: str):
        self.name = name
        self.info = info
        self.target_dir = Path(target_dir)
        self.conn = Connection(f"{info['username']}@{info['hostname']}:{info['port']}")
        # verify that connection works and that we get expected returns
        test_fabric_connection(conn=self.conn, hostname=info['hostname'], username=info['username'])

    

    def get_credentials(self):
        self.fc_user = os.getenv(self.name)
        self.fc_pass = os.getenv(f"{self.name}_P")
        write_to_file_remote(conn=self.conn,
                                          remote_path=str(self.target_dir / ".env"),
                                          content=f"FC_USER={self.fc_user}\nFC_PASS={self.fc_pass}\n")


    def transfer_data(self, target_dir: str, config_file: str):
        transfer_with_packing(conn=self.conn, paths=self.info['data'], remote_dir=target_dir)
        upload_file(conn=self.conn,local_path=config_file, remote_path=f"/home/user/config.toml", force=True)
        

