import paramiko
from fabric import SerialGroup

from fedsim.logger import log
from fedsim.utils import execute




class VagrantManager:


    def __init__(self, num_nodes: int, box: str = 'bento/ubuntu-24.04', provision_script: str = 'scripts/provision.sh'):
        """
        A class to manage Vagrant virtual machines for fedsim simulations.

        :param num_nodes: The number of nodes to use
        :param box: The Vagrant box to use
        :param provision_script: The path to the Vagrant provision script
        """
        # check dependencies
        assert self._vagrant_available()
        assert self._libvirt_available()
        self.num_nodes = num_nodes
        self.box = box
        self.provision_script = provision_script
        # initialized later
        self.client_strings = []
        self.serialg = []
        self.hosts = {}



    def _vagrant_available(self) -> bool:
        """
        Check if Vagrant is installed and available.

        :return: True if Vagrant is available, False otherwise.
        """        
        stdout, stderr = execute('vagrant --version')
        if 'Vagrant' in stdout:
            return True
        else:
            return False
        

    def _libvirt_available(self) -> bool:
        """
        Check if libvirt is installed and available.

        :return: True if libvirt is available, False otherwise.
        """
        stdout, stderr = execute('vagrant plugin list')
        if 'vagrant-libvirt' in stdout:
            return True
        else:
            return False
    
        

    def _write_vagrantfile(self) -> bool:
        """
        Dynamically write a vagrantfile given the configurable parts of the class's init.
        This avoids manual editing of the Vagrantfile for each different execution of fedsim.
        """
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
            return False
        log("Vagrantfile written")
        return True



    def _is_up(self) -> bool:
        """
        Check if the expected number of vagrant machines are up

        :return: True if all expected machines are up, False otherwise
        """
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



    def launch(self):
        """
        Bring the vagrant VMs up if they are not already running.
        This uses the dynamic Vagrantfile to adjust the number of VMs

        :raises RuntimeError: if Vagrant VMs fail to launch
        """
        is_up = self._is_up()
        if is_up:
            return
        try:
            # write dynamic vagrantfile
            self._write_vagrantfile()
            launch_cmd = 'vagrant up'
            stdout, stderr = execute(launch_cmd)
        except Exception as e:
            log(f"Error launching Vagrant VMs: {e}")
            raise RuntimeError("Vagrant VMs failed to launch.")
        # verify that vms are up
        is_up = self._is_up()
        if not is_up:
            raise RuntimeError("Vagrant VMs failed to launch.")
        


    def stop(self):
        """
        Stop vagrant machines if they are running
        """
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
    


    def _sshinfo(self) -> dict[str, dict]:
        """
        Get the ssh config of the vagrant VMs. 
        This is used to connect to them via fabric

        :return: A dictionary containing the SSH config for each VM
        """
        try:
            sshinfo_cmd = 'vagrant ssh-config'
            stdout, stderr = execute(sshinfo_cmd)
        except Exception as e:
            log(f"Error getting SSH info for Vagrant VMs: {e}")
            return {}
        
        hosts = self._parse_ssh_config(config_text=stdout)
        return hosts



    def _parse_ssh_config(self, config_text) -> dict[str, dict]:
        """
        Use paramiko to parse the ssh config info from vagrant

        :param config_text: ssh config text from vagrant
        :return: A dictionary containing the parsed SSH config
        """
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



    def _set_client_strings(self):
        """
        Create the client strings of the vagrant VMs for ssh access.
        I.e. user@hostname:port

        :return: A list of client strings for each VM
        """
        self.hosts = self._sshinfo()

        client_strings = []
        for host, info in self.hosts.items():
            cstr = f"{info['user']}@{info['hostname']}"
            if info['port'] is not None:
                cstr += f":{info['port']}"
            client_strings.append(cstr)
        # set as attribute and return
        self.client_strings = client_strings
        log(f"client strings: {self.client_strings}")
        return self.client_strings
    


    def construct_serialgroup(self):
        """
        Create the group of fabric Connections using the ssh info 
        and the ssh keys from vagrant

        :return: A fabric SerialGroup instance
        """
        # generate the client strings
        self._set_client_strings()
        # collect the ssh key files for each vm
        sshkeys = [info['identityfile'] for host, info in self.hosts.items()]
        serialg = SerialGroup(*self.client_strings, connect_kwargs={"key_filename": sshkeys})
        self.serialg = serialg
        return serialg



    def ping(self):
        """
        Test whether the VMs can be reached via the fabric Connections
        """
        # check if vms are up
        if not self._is_up():
            log("Vagrant VMs are not running.")
            return
        # check if serialgroup is constructed
        if not self.serialg:
            log("Constructing SerialGroup...")
            self.construct_serialgroup()
        # ping each vm
        for cxn in self.serialg:
            result = cxn.run('echo "Ping from $(hostname)"', hide=True)
        return

