from avocado import Test
from common.test_base import BaseContent_Test
from utils.ssh_utils import SSH
from utils.vm_utils import VM_Actions
from utils.yaml_utils import convert_yaml_to_dictionary

import avocado
import time
import logging


_logger = logging.getLogger(__name__)

class VmReboot_Test(BaseContent_Test):
    """
    TODO
    
    :avocado: enable
    """

    def setUp(self):
        """
        TODO
        """        
        super(VmReboot_Test, self).setUp()

        self.list_esxi_hosts = [
                {
                "platname": self.capi.suts[0],
                "esxi_host": self.ESXI_IP,
                "esxi_user": self.ESXI_USERNAME,
                "esxi_password": self.ESXI_PASSWORD,
                "nfs_datastore_name": "vce_nfs_server",
                "nfs_share_path": "/var/vce/virtual_machines_repository",
                "vms_names":[                    
                    "vm_clean_machine",                    
                    ],
                },
                {
                "platname": self.capi.suts[1],
                },
            ]
        self.platforms_checkup(self.list_esxi_hosts)

    def test_linux_vm_reboot(self):
        """
        PI_Virtualization_Reboot_V. Need to reboot these system using scripts for 100 times 
        and check the ping operations after each reboot.

        :avocado: tags=18014074603
        """   
        _logger.info( "TestCase.test_linux_vm_reboot: Init" )

        sut = self.list_esxi_hosts[0]

        vm_actions = VM_Actions(sut.get("esxi_host"), sut.get("esxi_user"), sut.get("esxi_password"))
        VMs = vm_actions.get_VM_names("vm_clean_machine", 1, 1)  

        vm_actions.power_on_vm(VMs)
        _logger.info( "Power-On Platform" )

        iterations = 5

        vm_ip = vm_actions.get_ip("vm_clean_machine")
        ##############################################################
        #Create tunnel for interacting with the platform
        ##############################################################
        hostname_capi = self.capi.targets[sut.get("platname")].rtb.parsed_url.hostname
        port = self.capi.targets[sut.get("platname")].tunnel.add(22, vm_ip )        

        for iteration in range(iterations):

            if vm_actions.power_off_vm(VMs) != 0:
                self.fail('powering on VM failed in iteration {}'.format(iteration))
            time.sleep(20)            
            _logger.info( "Power-Off Completed" )

            vm_actions.power_on_vm(VMs)
            _logger.info( "Power-On Completed" )
            
            esxi_vm_session = SSH(hostname_capi, "root", "intel@123", port)
            if not esxi_vm_session.is_remote_machine_alive(60):
                raise Exception('Failed to reboot VM (vm_clean_machine)')

        if vm_actions.power_off_vm(VMs) != 0:
            self.fail('powering on VM failed in iteration {}'.format(iteration))

        time.sleep(20)            
        _logger.info( "Power-Off Completed" )

        _logger.info( "TestCase.test_linux_vm_reboot: Completed" )