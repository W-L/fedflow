from pathlib import Path
import os

import pytest
from fedsim.VagrantManager import VagrantManager



@pytest.fixture
def vagrant_manager():    
    vm = VagrantManager(num_nodes=1)
    return vm
    
    
def test_vm_launch(vagrant_manager):
    vm = vagrant_manager
    vm.stop()
    assert not vm._is_up()
    vm.launch()
    assert Path("Vagrantfile").is_file()
    assert os.path.getsize("Vagrantfile") > 0
    assert vm._is_up()


def test_serialgroup(vagrant_manager):
    vm = vagrant_manager
    vm.launch()
    _ = vm.construct_serialgroup()

    expected_hosts = {
                "host": "nods-0",
                "hostname": "someip",
                "user": "vagrant",
                "port": 22,
                "identityfile": "path/to/private/key",
            }

    assert vm.hosts == expected_hosts
    assert vm.client_strings == ["vagrant@someip:22"]
    assert len(vm.serialg) == 1
    assert vm.serialg[0].host == "someip"

