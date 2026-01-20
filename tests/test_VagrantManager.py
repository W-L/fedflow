from pathlib import Path
import os
import pytest



@pytest.mark.integration
def test_vm_launch(vagrant_manager):
    vm = vagrant_manager
    Path("Vagrantfile").unlink(missing_ok=True)
    assert not Path("Vagrantfile").is_file()
    vm.halt()
    assert not vm._is_up()
    vm.launch()
    assert vm._is_up()
    assert Path("Vagrantfile").is_file()
    assert os.path.getsize("Vagrantfile") > 0



@pytest.mark.integration
def test_serialgroup(vagrant_manager):
    vm = vagrant_manager
    vm.launch()
    _ = vm.construct_connection_group()
    assert len(vm.hosts) == 3
    assert 'node-0' in list(vm.hosts.keys())
    assert vm.hosts['node-0']['user'] == 'vagrant'
    assert Path(vm.hosts['node-0']['identityfile']).is_file()
    assert len(vm.serialg) == 3
    assert vm.serialg[0].user == "vagrant"

