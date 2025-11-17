#%%
import paramiko
from fabric import SerialGroup

from logger import log
from utils import execute




class VagrantManager:
    """
    A class to manage Vagrant virtual machines for FedSim simulations.
    """
    def __init__(self, num_nodes: int):
        # check dependencies
        assert self.vagrant_available()
        assert self.libvirt_available()
        self.num_nodes = num_nodes
        self.box = 'bento/ubuntu-24.04'
        self.provision_script = 'VMs/vagrant_provision.sh'
        # initialized later
        self.client_strings = []
        self.serialg = []
        self.hosts = {}


    def vagrant_available(self) -> bool:
        """
        Check if Vagrant is installed and available.

        :return: True if Vagrant is available, False otherwise.
        """
        
        stdout, stderr = execute('vagrant --version')
        if 'Vagrant' in stdout:
            return True
        else:
            return False
        

    def libvirt_available(self) -> bool:
        """
        Check if libvirt is installed and available.

        :return: True if libvirt is available, False otherwise.
        """
        stdout, stderr = execute('vagrant plugin list')
        if 'vagrant-libvirt' in stdout:
            return True
        else:
            return False
    
        

    def _write_vagrantfile(self):
        vagrantfile_content = f"""

    ENV['VAGRANT_DEFAULT_PROVIDER'] = 'libvirt'

    Vagrant.configure("2") do |config|
        config.vm.box = '{self.box}'
        # disable mounting of cwd
        config.vm.synced_folder ".", "/vagrant", disabled: true

        (0..{self.num_nodes - 1}).each do |i|
            config.vm.define "node-#{{i}}" do |node|
                node.vm.hostname = "node-#{{i}}"
                # node.vm.synced_folder "./node-#{{i}}/", "/home/vagrant/node", create: true
                node.vm.provision "shell", name: "common", path: "{self.provision_script}"
            end
        end
    end
        """

        try:
            with open("Vagrantfile", "w") as vf:
                vf.write(vagrantfile_content)
                vf.write("\n")

        except Exception as e:
            log(f"Error writing Vagrantfile: {e}")
            return 1
        log("Vagrantfile written")
        return 0



    def _is_up(self) -> bool:
        vagrant_status = 'vagrant status | grep "running " | wc -l'
        
        # either vagrant is not up
        try:
            stdout, stderr = execute(vagrant_status)
        except Exception as e:
            log(f"Error executing Vagrant status command: {e}")
            return False

        # or an incorrect number of nodes are up
        count = int(stdout.strip())
        if count != self.num_nodes:
            log(f"Expected {self.num_nodes} nodes up, found {count}")
            return False
        # all good
        log(f"All {self.num_nodes} Vagrant nodes are running.")
        return True



    def launch(self) -> None:
        is_up = self._is_up()
        if is_up:
            return
        
        try:
            # write dynamic vagrantfile
            self._write_vagrantfile()
            # launch vms
            launch_cmd = 'vagrant up'
            stdout, stderr = execute(launch_cmd)
            
        except Exception as e:
            log(f"Error launching Vagrant VMs: {e}")
            return 
        
        # verify that vms are up
        is_up = self._is_up()
        if not is_up:
            raise RuntimeError("Vagrant VMs failed to launch.")
        return 


    def stop(self) -> None:
        if not self._is_up():
            log(f"Vagrant VMs are not running.")
            return

        try:
            stop_cmd = 'vagrant halt'
            stdout, stderr = execute(stop_cmd)
        except Exception as e:
            log(f"Error stopping Vagrant VMs: {e}")
            return 
        return
    


    def sshinfo(self) -> dict[str, dict]:
        try:
            sshinfo_cmd = 'vagrant ssh-config'
            stdout, stderr = execute(sshinfo_cmd)
        except Exception as e:
            log(f"Error getting SSH info for Vagrant VMs: {e}")
            return {}
        
        hosts = self._parse_ssh_config(config_text=stdout)
        return hosts





    def _parse_ssh_config(self, config_text):
        ssh_config = paramiko.SSHConfig()
        ssh_config.parse(config_text.splitlines())

        hosts = {}
        for host in ssh_config.get_hostnames():
            if host == '*':
                continue
            cfg = ssh_config.lookup(host)
            hosts[host] = {
                "host": host,
                "hostname": cfg.get("hostname"),
                "user": cfg.get("user"),
                "port": cfg.get("port"),
                "identityfile": list(cfg.get("identityfile", [None]))[0],
            }
        return hosts


    def set_client_strings(self):
        self.hosts = self.sshinfo()

        client_strings = []
        for host, info in self.hosts.items():
            cstr = f"{info['user']}@{info['hostname']}"
            if info['port'] is not None:
                cstr += f":{info['port']}"
            client_strings.append(cstr)

        self.client_strings = client_strings
        log(f"client strings: {self.client_strings}")
        return self.client_strings
    


    def construct_serialgroup(self):
        # generate the client strings
        self.set_client_strings()
        sshkeys = [info['identityfile'] for host, info in self.hosts.items()]
        serialg = SerialGroup(*self.client_strings, connect_kwargs={"key_filename": sshkeys})
        self.serialg = serialg
        return serialg


    def ping(self):
        if not self._is_up():
            log("Vagrant VMs are not running.")
            return

        if not self.serialg:
            log("Constructing SerialGroup...")
            self.construct_serialgroup()

        for cxn in self.serialg:
            result = cxn.run('echo "Ping from $(hostname)"', hide=True)
        return

#%%

# vms = VagrantManager(num_nodes=2)
# vms.launch()

#%%